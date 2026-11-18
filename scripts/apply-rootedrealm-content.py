#!/usr/bin/env python3
"""Load Rootedrealm legal copy from the exported Google Doc into page JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = Path(
    "/home/orion/.cursor/projects/home-orion-DevTag-RootedRealms/agent-tools/59ab77bb-72f1-49bf-b7db-30e67735cdce.txt"
)

MARKERS = [
    ("About Us", "about-us", "discover"),
    ("Our Commitment", "our-commitment", "discover"),
    ("Contact Us", "contact-us", "discover"),
    ("Frequently Asked Questions", "faqs", "discover"),
    ("Shipping & Delivery Policy", "shipping-policy", "customer-care"),
    ("Returns & Refunds Policy", "return-and-refund-policy", "customer-care"),
    ("Order Cancellation Policy", "cancellation-policy", "customer-care"),
    ("Payment Options", "payment-policy", "customer-care"),
    ("Warranty & Product Support", "warranty", "customer-care"),
    ("Order Help Center", "order-help-center", "customer-care"),
    ("Privacy Policy", "privacy-policy", "trust"),
    ("Terms of Service", "terms-of-service", "trust"),
    ("Cookie Policy", "cookie-policy", "trust"),
    ("Legal Notice", "legal-notice", "trust"),
    ("Accessibility Statement", "accessibility-statement", "trust"),
    ("Your Privacy Choices", "your-privacy-choices", "trust"),
]

TITLES = {
    "about-us": "About Us",
    "our-commitment": "Our Commitment",
    "contact-us": "Contact Us",
    "faqs": "FAQs",
    "shipping-policy": "Shipping & Delivery",
    "return-and-refund-policy": "Returns & Refunds",
    "cancellation-policy": "Order Cancellations",
    "payment-policy": "Payment Options",
    "warranty": "Warranty & Support",
    "order-help-center": "Order Help Center",
    "privacy-policy": "Privacy Policy",
    "terms-of-service": "Terms of Service",
    "cookie-policy": "Cookie Policy",
    "legal-notice": "Legal Notice",
    "accessibility-statement": "Accessibility Statement",
    "your-privacy-choices": "Your Privacy Choices",
}


def slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "section"


def clean_line(raw: str) -> str:
    line = raw.strip()
    if line.startswith("\ufeff"):
        line = line.lstrip("\ufeff").strip()
    if set(line) <= set("_-—– "):
        return ""
    return line


def parse_pages() -> dict[str, list[str]]:
    raw_lines = [clean_line(line) for line in DOC.read_text(encoding="utf-8").splitlines()]
    marker_map = {title: slug for title, slug, _ in MARKERS}
    pages: dict[str, list[str]] = {}
    current = None
    for line in raw_lines:
        if line in marker_map:
            current = marker_map[line]
            pages[current] = []
            continue
        if current is None or not line:
            continue
        pages[current].append(line)
    return pages


def first_sentence(lines: list[str], title: str) -> str:
    for line in lines:
        if line == title:
            continue
        if line.lower().startswith("last updated"):
            continue
        if line.startswith("* "):
            continue
        if len(line) > 40 and line.endswith("."):
            return line
    for line in lines:
        if len(line) > 20:
            return line
    return title


def tagline_from(lines: list[str], title: str) -> str:
    for line in lines:
        if line == title or line.lower().startswith("last updated"):
            continue
        if line.startswith("* ") or line[:1].isdigit():
            continue
        if len(line) < 90 and not line.endswith("."):
            return line
    return title


def intro_from(lines: list[str], description: str) -> list[str]:
    skip_until_body = True
    collected: list[str] = []
    for line in lines:
        if line.lower().startswith("last updated"):
            continue
        if skip_until_body and (len(line) < 80 and not line.endswith(".")):
            continue
        skip_until_body = False
        if line.startswith("* "):
            break
        collected.append(line)
        if line.endswith(".") and len(line) > 40:
            break
        if len(collected) >= 2:
            break
    return collected or [description]


def is_heading(line: str) -> bool:
    if line.startswith("* "):
        return False
    if re.match(r"^\d+\.\s+\S", line):
        return True
    if line.endswith("?"):
        return False
    if len(line) <= 90 and not line.endswith("."):
        return True
    return False


def sections_from_lines(lines: list[str]) -> list[dict]:
    sections: list[dict] = []
    current = {"id": "overview", "title": "", "blocks": []}

    def push():
        nonlocal current
        if current["blocks"] or current["title"]:
            if not current["id"]:
                current["id"] = slugify(current["title"] or "section")
            sections.append(current)
        current = {"id": "", "title": "", "blocks": []}

    for line in lines:
        if line.lower().startswith("last updated"):
            current["blocks"].append({"type": "paragraph", "text": line})
            continue
        if is_heading(line) and current["blocks"]:
            push()
            current = {"id": slugify(line), "title": line, "blocks": []}
            continue
        if is_heading(line) and not current["title"] and not current["blocks"]:
            current = {"id": slugify(line), "title": line, "blocks": []}
            continue
        if line.startswith("* "):
            current["blocks"].append({"type": "bullet", "text": line[2:]})
        else:
            current["blocks"].append({"type": "paragraph", "text": line})
    push()
    return sections or [{"id": "overview", "title": "", "blocks": [{"type": "paragraph", "text": ""}]}]


def faq_sections(lines: list[str]) -> tuple[list[dict], list[dict]]:
    groups: list[dict] = []
    group_title = "General Information"
    pending_q = None
    items: list[dict] = []

    def flush_group():
        nonlocal items, groups, group_title
        if items:
            groups.append({"title": group_title, "items": items})
            items = []

    body_started = False
    for line in lines:
        if line.lower().startswith("last updated"):
            continue
        if not body_started:
            if line.endswith(".") and len(line) > 40:
                body_started = True
            if is_heading(line) and not line.endswith("?"):
                group_title = line
                body_started = True
            continue
        if line.endswith("?"):
            pending_q = line
            continue
        if pending_q:
            items.append({"question": pending_q, "answer": line})
            pending_q = None
            continue
        if is_heading(line):
            flush_group()
            group_title = line
            continue
        if items:
            items[-1]["answer"] = f"{items[-1]['answer']} {line}"
    flush_group()

    preview_items = groups[0]["items"][:3] if groups else []
    sections = [
        {
            "id": "preview",
            "title": groups[0]["title"] if groups else "FAQs",
            "blocks": [
                {"type": "faq", "question": item["question"], "answer": item["answer"]}
                for item in preview_items
            ],
        }
    ]
    for group in groups:
        sections.append(
            {
                "id": slugify(group["title"]),
                "title": group["title"],
                "blocks": [
                    {"type": "faq", "question": item["question"], "answer": item["answer"]}
                    for item in group["items"]
                ],
            }
        )
    return sections, groups


def apply_file(path: Path, pages: dict[str, list[str]], slugs: set[str], faq_groups=None):
    data = json.loads(path.read_text())
    for page in data["pages"]:
        slug = page["slug"]
        if slug not in slugs:
            if slug == "buy-now-pay-later":
                # Keep the route. Strip the previous shop name from leftover copy.
                blob = json.dumps(page)
                blob = (
                    blob.replace("Vogueritual", "Rootedrealm")
                    .replace("vogueritual.us", "rootedrealm.com")
                    .replace("info@rootedrealm.com", "")
                    .replace("2260 Porter Way, Stockton, CA 95207", "3920 Gunn Hwy, Tampa, FL 33618")
                    .replace("+1 (209) 810-5789", "+1 (813) 963-6899")
                )
                page.update(json.loads(blob))
                page["title"] = "Buy Now, Pay Later"
            continue
        lines = pages[slug]
        title = TITLES[slug]
        description = first_sentence(lines, title)
        tagline = tagline_from(lines, title)
        intro = intro_from(lines, description)
        page["title"] = title
        page["tagline"] = tagline
        page["intro"] = intro
        page["description"] = description
        page["lines"] = lines
        if slug == "faqs":
            sections, groups = faq_sections(lines)
            page["sections"] = sections
            if faq_groups is not None:
                faq_groups.extend(groups)
        else:
            page["sections"] = sections_from_lines(lines)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_pages_json(pages: dict[str, list[str]], faq_groups: list[dict]):
    data = json.loads((ROOT / "data/pages.json").read_text())
    about = pages["about-us"]
    contact = pages["contact-us"]
    commitment = pages["our-commitment"]
    data["about"] = {
        "eyebrow": "About Rootedrealm",
        "title": "Welcome to Rootedrealm",
        "intro": first_sentence(about, "About Us"),
        "body": next(
            (line for line in about if line.startswith("We bring together")),
            first_sentence(about, "About Us"),
        ),
        "image": data["about"].get("image", ""),
        "values": [
            {
                "title": "A wide selection of products",
                "text": "Rootedrealm brings together electronics, outdoor equipment, home improvement, and lifestyle products in one place.",
            },
            {
                "title": "Free shipping across the United States",
                "text": "We offer free standard shipping on all orders throughout the USA, with no minimum order value.",
            },
            {
                "title": "Clear delivery estimates",
                "text": "Order processing is 1-2 business days, transit is 3-7 business days, and total estimated delivery is 4-9 business days.",
            },
            {
                "title": "30-day returns",
                "text": "Eligible defective and non-defective returns are accepted within 30 days, with free return shipping and no restocking fees.",
            },
            {
                "title": "Transparent shopping information",
                "text": "Product prices, shipping, returns, refunds, and payment methods are published before you buy.",
            },
        ],
        "sections": [
            {
                "title": "Who we are",
                "paragraphs": [
                    "Rootedrealm is a US-based multi-category online retail store operated by D & V Enterprises, Inc., located in Tampa, Florida.",
                    "Business address: 3920 Gunn Hwy, Tampa, FL 33618, United States.",
                ],
            },
            {
                "title": "What we offer",
                "paragraphs": [
                    "We bring together a diverse selection of products across electronics, gaming, computers, lawn and garden, outdoor living, home improvement, fireplaces, heating equipment, and wellness.",
                ],
            },
        ],
        "ctaTitle": "Explore more for your home, outdoors, and everyday life.",
        "ctaBody": "Shop electronics, outdoor equipment, fireplaces, saunas, and home products at Rootedrealm.",
    }
    data["contact"] = {
        "eyebrow": "Contact us",
        "title": "Get in Touch with Rootedrealm",
        "intro": first_sentence(contact, "Contact Us"),
        "channels": [
            {
                "title": "Phone",
                "detail": "+1 (813) 963-6899",
                "text": "Call +1 (813) 963-6899 during published customer service hours.",
            },
            {
                "title": "Hours",
                "detail": "Monday-Friday, 9:00 AM-5:00 PM",
                "text": "Customer service is available Monday through Friday, 9:00 AM-5:00 PM.",
            },
            {
                "title": "Address",
                "detail": "3920 Gunn Hwy, Tampa, FL 33618, United States",
                "text": "Rootedrealm is operated by D & V Enterprises, Inc. at 3920 Gunn Hwy, Tampa, FL 33618, United States.",
            },
        ],
        "businessNote": "Business address: Rootedrealm, D & V Enterprises, Inc., 3920 Gunn Hwy, Tampa, FL 33618, United States. Do not send merchandise to this address without return instructions.",
        "helpTopics": [
            {"title": "Product questions", "text": "Contact us for information about product specifications, dimensions, compatibility, and availability."},
            {"title": "Order assistance", "text": "If you have already placed an order, please have your order number available when contacting us."},
            {"title": "Shipping and delivery", "text": "Standard shipping is free throughout the United States. Handling 1-2 business days. Transit 3-7 business days. Total estimated delivery 4-9 business days."},
            {"title": "Returns and refunds", "text": "Eligible defective and non-defective returns are accepted within 30 days, with free return shipping and no restocking fees. Direct exchanges are not available."},
            {"title": "Damaged or incorrect products", "text": "Contact customer service and provide your order number, a description of the problem, and photographs where available."},
        ],
        "formNote": "Recommended contact form fields: Full Name, Email Address, Phone Number (Optional), Order Number (If Applicable), Inquiry Type, Message.",
        "securityNote": "Please do not submit complete payment card numbers, security codes, or passwords.",
        "hours": [
            {"channel": "Phone", "availability": "+1 (813) 963-6899"},
            {"channel": "Customer service hours", "availability": "Monday-Friday, 9:00 AM-5:00 PM"},
            {"channel": "Standard shipping", "availability": "Free throughout the USA"},
            {"channel": "Estimated delivery", "availability": "4-9 business days"},
        ],
        "faqs": [
            {"question": "What is Rootedrealm?", "answer": "Rootedrealm is a US-based multi-category online retailer operated by D & V Enterprises, Inc."},
            {"question": "Where is Rootedrealm located?", "answer": "Our published business address is 3920 Gunn Hwy, Tampa, FL 33618, United States."},
            {"question": "How can I contact customer support?", "answer": "Call +1 (813) 963-6899 during our published customer service hours."},
            {"question": "Do you offer free shipping?", "answer": "Yes. Standard shipping is free throughout the United States."},
            {"question": "What is your return window?", "answer": "30 days."},
            {"question": "What payment methods do you accept?", "answer": "The payment methods currently supported are displayed at checkout."},
        ],
    }
    data["commitment"] = {
        "eyebrow": "Our commitment",
        "title": "Shopping with Clarity and Confidence",
        "intro": first_sentence(commitment, "Our Commitment"),
        "body": "We offer products across electronics, computers, gaming, lawn and garden, outdoor power equipment, fireplaces, wood stoves, saunas, and home improvement.",
        "sections": [
            {"title": item["title"], "paragraphs": [block["text"] for block in item["blocks"] if block["type"] == "paragraph"], "bullets": [block["text"] for block in item["blocks"] if block["type"] == "bullet"]}
            for item in sections_from_lines(commitment)
            if item["title"]
        ],
        "ctaTitle": "Contact Rootedrealm",
        "ctaBody": "Rootedrealm, operated by D & V Enterprises, Inc., 3920 Gunn Hwy, Tampa, FL 33618, United States. Phone: +1 (813) 963-6899. Hours: Monday-Friday, 9:00 AM-5:00 PM.",
    }
    data["faq"] = {
        "eyebrow": "FAQs",
        "title": "Frequently asked questions",
        "intro": first_sentence(pages["faqs"], "FAQs"),
        "groups": faq_groups
        or [
            {
                "title": "General Information",
                "items": [
                    {
                        "question": "What is Rootedrealm?",
                        "answer": "Rootedrealm is a US-based multi-category online retailer operated by D & V Enterprises, Inc.",
                    }
                ],
            }
        ],
    }
    (ROOT / "data/pages.json").write_text(json.dumps(data, indent=2) + "\n")


def main():
    pages = parse_pages()
    missing = [slug for _, slug, _ in MARKERS if slug not in pages]
    if missing:
        raise SystemExit(f"Missing tabs/sections: {missing}")
    for slug, lines in pages.items():
        print(f"{slug}: {len(lines)} lines")
    faq_groups: list[dict] = []
    apply_file(
        ROOT / "data/discover/pages.json",
        pages,
        {"about-us", "our-commitment", "contact-us", "faqs"},
        faq_groups,
    )
    apply_file(
        ROOT / "data/customer-care/pages.json",
        pages,
        {
            "shipping-policy",
            "return-and-refund-policy",
            "cancellation-policy",
            "payment-policy",
            "warranty",
            "order-help-center",
        },
    )
    apply_file(
        ROOT / "data/trust/pages.json",
        pages,
        {
            "privacy-policy",
            "terms-of-service",
            "cookie-policy",
            "legal-notice",
            "accessibility-statement",
            "your-privacy-choices",
        },
    )
    update_pages_json(pages, faq_groups)
    print("updated JSON content")


if __name__ == "__main__":
    main()
