"""
mock_emails.py
==============
Base de datos mock — SOLO datos, cero lógica.

Añade emails nuevos copiando cualquier bloque existente y cambiando:
  · "id"              → siguiente número (msg_011, msg_012 ...)
  · "threadId"        → mismo valor que id
  · "internalDate"    → epoch ms (https://www.epochconverter.com)
  · headers           → Subject, From, To, Date
  · "body_text_content" → texto con el ruido que quieras probar

Reglas para que el pipeline funcione correctamente:
  · El id debe ser único.
  · Los headers DEBEN incluir al menos Subject, From y Date.
  · body_text_content es el texto bruto que se guarda en data/raw/<id>.txt
"""

MOCK_EMAILS: list[dict] = [

    # ── msg_001 · Queja urgente con HTML, firma, hilo y disclaimer ─────────
    {
        "id": "msg_001",
        "threadId": "msg_001",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "I have asked for a refund three times now...",
        "internalDate": "1740038100000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "URGENT: REFUND REQUEST - ORDER #998822"},
                {"name": "From",    "value": "angry.customer@example.com"},
                {"name": "To",      "value": "support@techcompany.com"},
                {"name": "Date",    "value": "Thu, 20 Feb 2026 09:15:00 +0000"},
            ]
        },
        "body_text_content": """
<div><b>URGENT:</b> Please &nbsp; read this immediately!</div>
<p>I have asked for a refund <b>three times</b> now! Your service is completely broken.</p>

I expect a call at +1 (555) 010-9988 or email me at admin@personal.net.

Check my order status here: https://portal.techcompany.com/orders/998822

> On Mon, Feb 10, 2026 at 9:00 AM, Support <support@techcompany.com> wrote:
> > Thank you for contacting us. We are looking into your request.
> >
> > On Thu, Feb 05, 2026 at 3:00 PM, angry.customer wrote:
> > > I need a refund NOW. This is unacceptable.

---------- Forwarded message ---------
From: Billing Department <billing@techcompany.com>
Date: Sun, Feb 09, 2026
Subject: Invoice #998822

Your invoice is attached.

--
Sent from my iPhone

This email and any attachments are confidential and intended solely for the use of
the individual or entity to which they are addressed.
""",
    },

    # ── msg_002 · Cancelación de cuenta, tono muy negativo ─────────────────
    {
        "id": "msg_002",
        "threadId": "msg_002",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "I cannot believe how buggy this software is...",
        "internalDate": "1740124200000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Complete waste of time - Cancel my account"},
                {"name": "From",    "value": "dissatisfied@corp.net"},
                {"name": "To",      "value": "support@techcompany.com"},
                {"name": "Date",    "value": "Fri, 21 Feb 2026 14:30:00 +0000"},
            ]
        },
        "body_text_content": """I cannot believe how buggy this software is. I've lost 3 hours of work today.

Every time I try to export my report I get a blank page. This is completely unacceptable for
a paying customer. Cancel my subscription NOW.

I expect a written confirmation within the hour.

> On Thu, Feb 20, 2026 at 8:00 PM, Support wrote:
> > We apologise for the inconvenience. Our team is working on it.

CONFIDENTIAL: This message is for the named person's use only.
""",
    },

    # ── msg_003 · Seguimiento propuesta comercial, hilo largo ───────────────
    {
        "id": "msg_003",
        "threadId": "msg_003",
        "labelIds": ["INBOX"],
        "snippet": "Just following up on my previous email from last week...",
        "internalDate": "1739606400000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Re: Re: Partnership Proposal — Q1 2026"},
                {"name": "From",    "value": "partner@business.com"},
                {"name": "To",      "value": "sales@techcompany.com"},
                {"name": "Date",    "value": "Sun, 15 Feb 2026 10:00:00 +0000"},
            ]
        },
        "body_text_content": """Hi Sarah,

Just following up on my previous email from last week. Have you had a chance to review
the proposal we sent over? We are really excited about this partnership opportunity.

Best regards,
Marcus
Partner Success @ Business.com
Tel: +44 20 7946 0123 | www.business.com

> On Mon, Feb 10, 2026 at 9:00 AM, Sarah <sales@techcompany.com> wrote:
> > Hi Marcus, thanks for sending this over. We will review it internally and get back to you.
> >
> > On Thu, Feb 06, 2026 at 2:00 PM, Marcus wrote:
> > > Dear Sarah, please find attached our partnership proposal for Q1 2026.

--
This e-mail is intended only for the use of the individual(s) named above.
""",
    },

    # ── msg_004 · Seguimiento ticket soporte sin respuesta ──────────────────
    {
        "id": "msg_004",
        "threadId": "msg_004",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "I haven't heard back regarding the login issue...",
        "internalDate": "1739177100000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Checking in on ticket #5544"},
                {"name": "From",    "value": "john.doe@users.com"},
                {"name": "To",      "value": "support@techcompany.com"},
                {"name": "Date",    "value": "Mon, 10 Feb 2026 08:45:00 +0000"},
            ]
        },
        "body_text_content": """Hello Support Team,

I haven't heard back regarding the login issue I reported on ticket #5544. Is there any update?
It's been 5 days and I still cannot access my account.

My account email is: john.doe@users.com

Best regards,
John Doe

> On Wed, Feb 05, 2026 at 11:00 AM, Support wrote:
> > Hi John, we have received your ticket and will respond within 2 business days.

Sent from Outlook for iOS
""",
    },

    # ── msg_005 · Feedback positivo con petición de funcionalidad ───────────
    {
        "id": "msg_005",
        "threadId": "msg_005",
        "labelIds": ["INBOX"],
        "snippet": "I really like the new design! However, it would be great...",
        "internalDate": "1740220800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Feedback on the new dashboard prototype"},
                {"name": "From",    "value": "beta.tester@innovate.io"},
                {"name": "To",      "value": "product@techcompany.com"},
                {"name": "Date",    "value": "Sat, 22 Feb 2026 11:20:00 +0000"},
            ]
        },
        "body_text_content": """Hey team,

I really like the new design! The layout is much cleaner and the load times are noticeably faster.

However, it would be great if we could export the charts to CSV format directly from the dashboard.
Is that something you could add to the roadmap?

Cheers,
Alex
Beta Tester — Innovate.io
https://innovate.io | @alex_tests
""",
    },

    # ── msg_006 · Idea feature: dark mode, firma móvil ──────────────────────
    {
        "id": "msg_006",
        "threadId": "msg_006",
        "labelIds": ["INBOX"],
        "snippet": "I love the app but my eyes hurt at night...",
        "internalDate": "1740009600000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Idea: Dark Mode for the web app"},
                {"name": "From",    "value": "night.owl@creative.com"},
                {"name": "To",      "value": "feedback@techcompany.com"},
                {"name": "Date",    "value": "Wed, 19 Feb 2026 23:00:00 +0000"},
            ]
        },
        "body_text_content": """I love the app but my eyes hurt at night when using it for long sessions.

Please please please add a dark mode option! Even a simple toggle in settings would do.

Sent from my iPhone

________________________________
DISCLAIMER: The information in this email is confidential and may be legally privileged.
""",
    },

    # ── msg_007 · Bug report con steps to reproduce ─────────────────────────
    {
        "id": "msg_007",
        "threadId": "msg_007",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Steps to reproduce: 1. Go to settings...",
        "internalDate": "1740232800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Bug: 500 Error when uploading avatar"},
                {"name": "From",    "value": "qa.external@testing.com"},
                {"name": "To",      "value": "bugs@techcompany.com"},
                {"name": "Date",    "value": "Sat, 22 Feb 2026 15:00:00 +0000"},
            ]
        },
        "body_text_content": """Hi Engineering Team,

**Steps to reproduce:**
1. Go to Settings → Profile
2. Click "Upload avatar"
3. Select any .png file
4. Click "Save"
5. HTTP 500 Internal Server Error appears immediately

**Expected:** Avatar saved. **Actual:** 500 error, no upload.
**Environment:** Chrome 121, Windows 10, Admin account.

Regards,
QA External Team | qa.external@testing.com
""",
    },

    # ── msg_008 · Crash en startup con log redactado ─────────────────────────
    {
        "id": "msg_008",
        "threadId": "msg_008",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "The app crashes immediately after the splash screen...",
        "internalDate": "1740069900000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Crash on startup (Windows 11)"},
                {"name": "From",    "value": "win.user@legacy.com"},
                {"name": "To",      "value": "support@techcompany.com"},
                {"name": "Date",    "value": "Thu, 20 Feb 2026 16:45:00 +0000"},
            ]
        },
        "body_text_content": """Hello,

The app crashes immediately after the splash screen on my Windows 11 machine (22H2).
I have tried reinstalling twice — same result.

[LOG CONTENT REDACTED FOR PRIVACY]

--
Win User | win.user@legacy.com

> This email is a reply to ticket AUTO-8821 opened via our support portal.

CONFIDENTIALITY NOTICE: This email may contain confidential information.
""",
    },

    # ── msg_009 · Consulta enterprise pricing ───────────────────────────────
    {
        "id": "msg_009",
        "threadId": "msg_009",
        "labelIds": ["INBOX"],
        "snippet": "We are interested in the enterprise plan...",
        "internalDate": "1739875800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Question about Enterprise pricing"},
                {"name": "From",    "value": "cto@bigcorp.com"},
                {"name": "To",      "value": "sales@techcompany.com"},
                {"name": "Date",    "value": "Tue, 18 Feb 2026 09:30:00 +0000"},
            ]
        },
        "body_text_content": """Hi Sales Team,

We are evaluating your product for our organisation and would like to know:

1. Volume discounts for 50+ seats?
2. SSO (SAML 2.0) supported out of the box?
3. On-premise hosting option?

Budget deadline: March 15, 2026.

Thanks,
Richard Chen · CTO @ BigCorp
richard.chen@bigcorp.com | +1 (415) 555-0192
""",
    },

    # ── msg_010 · Invitación evento con URL y HTML ligero ───────────────────
    {
        "id": "msg_010",
        "threadId": "msg_010",
        "labelIds": ["INBOX"],
        "snippet": "We would like to invite you to speak at Tech Summit 2026...",
        "internalDate": "1737806400000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Invitation: Tech Summit 2026 — Speaker Opportunity"},
                {"name": "From",    "value": "organizer@techsummit.com"},
                {"name": "To",      "value": "info@techcompany.com"},
                {"name": "Date",    "value": "Sat, 25 Jan 2026 12:00:00 +0000"},
            ]
        },
        "body_text_content": """Dear TechCompany Team,

<p>We would like to <strong>invite you</strong> to speak at <em>Tech Summit 2026</em>.</p>

April 10–12, 2026 · San Francisco, CA · 2,000+ attendees.

Register: https://techsummit.com/register?ref=techcompany&utm_source=email&utm_campaign=speakers_2026

Best,
The Tech Summit Organising Committee

--
To unsubscribe: https://techsummit.com/unsubscribe?token=abc123xyz
""",
    },

    # ══════════════════════════════════════════════════════════════════════
    # AÑADE TUS EMAILS AQUÍ — copia el bloque de abajo, cambia los campos
    # ══════════════════════════════════════════════════════════════════════
    #
    # {
    #     "id": "msg_011",
    #     "threadId": "msg_011",
    #     "labelIds": ["INBOX", "UNREAD"],
    #     "snippet": "Breve descripción del email...",
    #     "internalDate": "1740300000000",   # epoch ms en string
    #     "payload": {
    #         "headers": [
    #             {"name": "Subject", "value": "Asunto del email"},
    #             {"name": "From",    "value": "remitente@dominio.com"},
    #             {"name": "To",      "value": "destinatario@techcompany.com"},
    #             {"name": "Date",    "value": "Sun, 23 Feb 2026 10:00:00 +0000"},
    #         ]
    #     },
    #     "body_text_content": """Cuerpo del email con todo el ruido que quieras.
    #
    # Puedes incluir HTML, firmas, hilos con >, disclaimers, URLs...
    #
    # --
    # Firma del remitente
    # """,
    # },

]