"""Email Sequence Builder — Flask Blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps

from database.manage_sequences import (
    create_sequence, get_all_sequences, get_sequence,
    get_steps, add_step, delete_step, delete_sequence, enroll_contact,
)
from database.manage_contacts import get_contact

sequence_bp = Blueprint("sequences", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def sanitize_input(value, max_length=500):
    if not value:
        return ""
    return str(value).strip()[:max_length]


@sequence_bp.route("/sequences")
@login_required
def sequences_list():
    seqs = get_all_sequences()
    return render_template("sequences.html", sequences=seqs)


@sequence_bp.route("/sequences/create", methods=["POST"])
@login_required
def sequences_create():
    name = sanitize_input(request.form.get("name", ""))
    description = sanitize_input(request.form.get("description", ""), max_length=500)
    if not name:
        flash("Sequence name is required.", "error")
        return redirect(url_for("sequences.sequences_list"))
    seq_id = create_sequence(name, description)
    if seq_id:
        flash(f"Sequence '{name}' created.", "success")
        return redirect(url_for("sequences.sequences_detail", seq_id=seq_id))
    else:
        flash(f"A sequence named '{name}' already exists.", "error")
        return redirect(url_for("sequences.sequences_list"))


@sequence_bp.route("/sequences/<int:seq_id>")
@login_required
def sequences_detail(seq_id):
    seq = get_sequence(seq_id)
    if not seq:
        flash("Sequence not found.", "error")
        return redirect(url_for("sequences.sequences_list"))
    steps = get_steps(seq_id)
    next_step_number = (max(s["step_number"] for s in steps) + 1) if steps else 1
    return render_template(
        "sequence_detail.html",
        seq=seq,
        steps=steps,
        next_step_number=next_step_number,
    )


@sequence_bp.route("/sequences/<int:seq_id>/add-step", methods=["POST"])
@login_required
def sequences_add_step(seq_id):
    seq = get_sequence(seq_id)
    if not seq:
        flash("Sequence not found.", "error")
        return redirect(url_for("sequences.sequences_list"))
    try:
        step_number = int(request.form.get("step_number", 1))
        delay_days  = int(request.form.get("delay_days", 0))
    except ValueError:
        flash("Step number and delay must be numbers.", "error")
        return redirect(url_for("sequences.sequences_detail", seq_id=seq_id))
    subject = sanitize_input(request.form.get("subject_template", ""), max_length=500)
    body    = sanitize_input(request.form.get("body_template", ""), max_length=5000)
    if not subject or not body:
        flash("Subject and body are required.", "error")
        return redirect(url_for("sequences.sequences_detail", seq_id=seq_id))
    add_step(seq_id, step_number, delay_days, subject, body)
    flash(f"Step {step_number} added (send after {delay_days} day(s)).", "success")
    return redirect(url_for("sequences.sequences_detail", seq_id=seq_id))


@sequence_bp.route("/sequences/<int:seq_id>/delete-step/<int:step_id>", methods=["POST"])
@login_required
def sequences_delete_step(seq_id, step_id):
    delete_step(step_id)
    flash("Step deleted.", "success")
    return redirect(url_for("sequences.sequences_detail", seq_id=seq_id))


@sequence_bp.route("/sequences/<int:seq_id>/delete", methods=["POST"])
@login_required
def sequences_delete(seq_id):
    seq = get_sequence(seq_id)
    if seq:
        delete_sequence(seq_id)
        flash(f"Sequence '{seq['name']}' deleted.", "success")
    return redirect(url_for("sequences.sequences_list"))


@sequence_bp.route("/sequences/<int:seq_id>/enroll/<int:contact_id>/<int:domain_id>", methods=["POST"])
@login_required
def sequences_enroll(seq_id, contact_id, domain_id):
    ok = enroll_contact(seq_id, contact_id, domain_id)
    if ok:
        contact = get_contact(contact_id)
        flash(f"Enrolled {contact['name'] if contact else 'contact'} in sequence.", "success")
    else:
        flash("Contact is already enrolled in this sequence.", "info")
    return redirect(request.referrer or url_for("sequences.sequences_list"))
