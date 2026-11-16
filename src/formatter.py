"""Report formatting in Table and CSV formats."""

import csv
import io
from decimal import Decimal
from src.models import ReportResult


def format_rub(amount: Decimal) -> str:
    """Format decimal amount into Russian rubles with space thousands separator."""
    return f"{amount:,.2f}".replace(",", " ")


def format_table_report(result: ReportResult) -> str:
    """Format settlement result into an aligned human-readable terminal table."""
    lines: list[str] = []
    width = 90
    border = "=" * width
    sub_border = "-" * width

    lines.append(border)
    lines.append(f"ФИНАНСОВЫЙ ОТЧЁТ ПО ДОГОВОРАМ И РАБОТАМ (на дату: {result.cutoff_date.strftime('%d.%m.%Y')})")
    lines.append(border)

    if not result.contracts:
        lines.append("Нет действующих договоров на указанную дату.")
        lines.append(border)
        return "\n".join(lines)

    for i, c in enumerate(result.contracts):
        if i > 0:
            lines.append("")

        lines.append(f"ДОГОВОР: {c.contract_id} | Подрядчик: {c.contractor} | Подписан: {c.signed_at.strftime('%d.%m.%Y')}")
        lines.append(
            f"  Сумма договора: {format_rub(c.signed_amount):>12} руб.  |  Сумма активных работ: {format_rub(c.active_works_total):>12} руб."
        )
        lines.append(
            f"  Всего выплачено: {format_rub(c.total_paid):>11} руб.  |  Остаток к оплате:     {format_rub(c.remaining_payable):>12} руб."
        )
        lines.append(f"  Нераспределённый аванс: {format_rub(c.unallocated_advance):>7} руб.")

        if c.warning:
            lines.append(f"  [ВНИМАНИЕ] {c.warning}")

        lines.append(sub_border)
        header = f"{'Код':<7} | {'Название работы':<32} | {'Статус':<9} | {'Цена (руб.)':>12} | {'Выплачено':>12} | {'Остаток':>12}"
        lines.append(header)
        lines.append(sub_border)

        for w in c.works:
            title_truncated = (w.title[:29] + "...") if len(w.title) > 32 else w.title
            row = (
                f"{w.work_id:<7} | "
                f"{title_truncated:<32} | "
                f"{w.effective_status:<9} | "
                f"{format_rub(w.price):>12} | "
                f"{format_rub(w.total_paid):>12} | "
                f"{format_rub(w.remaining_payable):>12}"
            )
            lines.append(row)
        lines.append(sub_border)

    lines.append("")
    lines.append(border)
    lines.append("ИТОГО ПО ВСЕМ ДОГОВОРАМ:")
    lines.append(f"  Сумма договоров:         {format_rub(result.grand_total_signed):>14} руб.")
    lines.append(f"  Всего выплачено:         {format_rub(result.grand_total_paid):>14} руб.")
    lines.append(f"  Остаток к оплате:        {format_rub(result.grand_total_remaining):>14} руб.")
    lines.append(f"  Нераспределённый аванс:  {format_rub(result.grand_total_unallocated):>14} руб.")
    lines.append(border)

    if result.warnings:
        lines.append("")
        lines.append("ПРЕДУПРЕЖДЕНИЯ ДЛЯ БУХГАЛТЕРИИ:")
        for w in result.warnings:
            lines.append(f"  • {w}")
        lines.append(border)

    return "\n".join(lines)


def format_csv_report(result: ReportResult) -> str:
    """Format settlement result as CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    writer.writerow([
        "contract_id",
        "contractor",
        "contract_signed_at",
        "contract_amount",
        "contract_paid",
        "contract_remaining",
        "contract_unallocated_advance",
        "work_id",
        "work_title",
        "work_status_on_date",
        "work_price",
        "work_direct_paid",
        "work_advance_allocated",
        "work_total_paid",
        "work_remaining",
    ])

    for c in result.contracts:
        for w in c.works:
            writer.writerow([
                c.contract_id,
                c.contractor,
                c.signed_at.isoformat(),
                f"{c.signed_amount:.2f}",
                f"{c.total_paid:.2f}",
                f"{c.remaining_payable:.2f}",
                f"{c.unallocated_advance:.2f}",
                w.work_id,
                w.title,
                w.effective_status,
                f"{w.price:.2f}",
                f"{w.direct_paid:.2f}",
                f"{w.advance_allocated:.2f}",
                f"{w.total_paid:.2f}",
                f"{w.remaining_payable:.2f}",
            ])

    return output.getvalue()
