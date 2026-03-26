from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from .forms import ContactoForm
from .models import db, ContactMessage
import os

main = Blueprint("main", __name__)


@main.route("/sw.js")
def service_worker():
    """Serve service worker from root for full scope."""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'sw.js',
        mimetype='application/javascript'
    )


@main.route("/manifest.json")
def manifest():
    """Serve manifest from root for PWA."""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'manifest.json',
        mimetype='application/manifest+json'
    )


@main.route("/", methods=["GET"])
def index():
    # Muestra la landing con el formulario
    form = ContactoForm()
    return render_template("index.html", form=form)


@main.route("/contacto", methods=["POST"])
def contacto():
    form = ContactoForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            nombre=form.nombre.data,
            email=form.email.data,
            telefono=form.telefono.data,
            empresa=form.empresa.data,
            mensaje=form.mensaje.data,
        )
        db.session.add(msg)
        db.session.commit()
        flash("✅ Tu mensaje fue enviado con éxito", "success")

        # Redirige a la misma página donde se envió el form
        next_page = request.referrer or url_for("main.index")
        return redirect(next_page + "#contacto")

    # 👇 Esto imprime los errores de validación en la consola
    print(form.errors)
    flash("⚠️ Hay errores en el formulario", "danger")

    # Si falla, vuelve a la página de origen (index o servicios)
    template = "services.html" if "servicios" in (request.referrer or "") else "index.html"
    return render_template(template, form=form), 400


@main.route("/servicios", methods=["GET"])
def servicios():
    # Página de servicios con el formulario también
    form = ContactoForm()
    return render_template("services.html", form=form)



