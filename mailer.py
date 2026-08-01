# mailer.py
# Simple, secure SMTP-based mailer with templates and error handling
import smtplib
import ssl
import socket
from email.message import EmailMessage
from flask import current_app, render_template
import logging

logger = logging.getLogger(__name__)


def init_app(app):
    """Initialize mailer and validate SMTP configuration at startup."""
    app.extensions = getattr(app, "extensions", {})
    app.extensions["mailer_initialized"] = True

    # Startup config validation — surface misconfiguration immediately in logs
    required_vars = {
        "SMTP_HOST": app.config.get("SMTP_HOST"),
        "SMTP_USERNAME": app.config.get("SMTP_USERNAME"),
        "SMTP_PASSWORD": app.config.get("SMTP_PASSWORD"),
        "SMTP_FROM": app.config.get("SMTP_FROM"),
    }
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        app.logger.warning(
            "SMTP configuration incomplete — the following environment "
            "variables are missing or empty: %s. Emails will NOT be sent "
            "until these are set.",
            ", ".join(missing),
        )
    else:
        app.logger.info(
            "SMTP mailer configured: host=%s, port=%s, from=%s",
            app.config.get("SMTP_HOST"),
            app.config.get("SMTP_PORT"),
            app.config.get("SMTP_FROM"),
        )


def send_email(to_address, subject, template_base, context=None):
    """Send an email to a recipient.
    template_base is the base name of a template in templates/ (e.g. 'welcome_email').
    context is a dict passed to render_template for both text and html.
    Returns True on success, False on failure.
    """
    context = context or {}
    try:
        app = current_app._get_current_object()
    except RuntimeError:
        logger.error("No Flask application context available for sending email")
        return False

    smtp_host = app.config.get("SMTP_HOST")
    smtp_port = int(app.config.get("SMTP_PORT", 587))
    smtp_user = app.config.get("SMTP_USERNAME")
    smtp_pass = app.config.get("SMTP_PASSWORD")
    smtp_from = app.config.get("SMTP_FROM", smtp_user)
    use_ssl = app.config.get("SMTP_USE_SSL", False)
    use_tls = app.config.get("SMTP_USE_TLS", True)

    # Runtime config validation
    missing = []
    if not smtp_host:
        missing.append("SMTP_HOST")
    if not smtp_user:
        missing.append("SMTP_USERNAME")
    if not smtp_pass:
        missing.append("SMTP_PASSWORD")
    if missing:
        app.logger.error("SMTP configuration missing: %s. Email not sent to %s", ", ".join(missing), to_address)
        return False

    # Render templates — templates live directly in templates/ (no emails/ subfolder)
    text_body = None
    html_body = None
    try:
        text_body = render_template(f"{template_base}.txt", **context)
    except Exception as ex:
        app.logger.debug("Text template %s.txt not found or failed to render: %s", template_base, ex)
    try:
        html_body = render_template(f"{template_base}.html", **context)
    except Exception as ex:
        app.logger.debug("HTML template %s.html not found or failed to render: %s", template_base, ex)

    if not text_body and not html_body:
        app.logger.error("No email templates found for '%s' (looked for templates/%s.txt and templates/%s.html)", template_base, template_base, template_base)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_address

    if html_body and text_body:
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
    elif html_body:
        # If only HTML is present set a plain text fallback
        msg.set_content("Please view this email in an HTML-capable client.")
        msg.add_alternative(html_body, subtype="html")
    else:
        msg.set_content(text_body)

    try:
        if use_ssl:
            context_ssl = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context_ssl) as server:
                # Some SMTP servers (e.g., local debug servers) do not support AUTH.
                # Only attempt login if credentials are provided and the server supports the AUTH extension.
                if smtp_user and smtp_pass and server.has_extn('auth'):
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                # Some servers require EHLO before STARTTLS; ensure it's called implicitly
                server.ehlo()
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if smtp_user and smtp_pass and server.has_extn('auth'):
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        app.logger.info("Email sent to %s: %s", to_address, subject)
        return True
    except smtplib.SMTPAuthenticationError as e:
        app.logger.error(
            "SMTP authentication failed when sending to %s — check SMTP_USERNAME "
            "and SMTP_PASSWORD (for Brevo, the password must be the SMTP key from "
            "your Brevo dashboard, not your account login password). "
            "Server response: %s %s",
            to_address, e.smtp_code, e.smtp_error,
        )
        return False
    except smtplib.SMTPConnectError as e:
        app.logger.error(
            "Could not connect to SMTP server %s:%s — check SMTP_HOST and "
            "SMTP_PORT. Error: %s %s",
            smtp_host, smtp_port, e.smtp_code, e.smtp_error,
        )
        return False
    except smtplib.SMTPServerDisconnected as e:
        app.logger.error(
            "SMTP server %s:%s disconnected unexpectedly. This may indicate a "
            "TLS/SSL mismatch (try toggling SMTP_USE_TLS / SMTP_USE_SSL). Error: %s",
            smtp_host, smtp_port, e,
        )
        return False
    except (socket.timeout, TimeoutError) as e:
        app.logger.error(
            "Timeout connecting to SMTP server %s:%s — the host may be "
            "unreachable or the port may be blocked. Error: %s",
            smtp_host, smtp_port, e,
        )
        return False
    except Exception as e:
        app.logger.exception("Failed to send email to %s. Error: %s", to_address, str(e))
        return False
