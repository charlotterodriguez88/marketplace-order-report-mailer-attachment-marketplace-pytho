from .models import OrderHandoffRequest


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def render_handoff_pdf(order: OrderHandoffRequest) -> bytes:
    lines = [
        "Marketplace order handoff",
        f"Order: {order.order_id}",
        f"Seller: {order.seller.display_name}",
        f"Buyer: {order.buyer.name}",
        "Assets:",
        *[f"- {asset.title} [{asset.media_type}]" for asset in order.assets],
        "Buyer updates:",
        *[f"- {update.title} ({update.published_at})" for update in order.updates],
    ]
    if not order.updates:
        lines.append("- No updates published")

    commands = []
    for index, line in enumerate(lines):
        y = 750 - index * 24
        commands.append(f"BT /F1 12 Tf 54 {y} Td ({_escape_pdf_text(line)}) Tj ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(pdf)

