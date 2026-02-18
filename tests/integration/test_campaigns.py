from datetime import datetime, timedelta

import pytest
from rich.console import Console

from ozon_api_sdk.base import ReportPollingProgress

pytestmark = [pytest.mark.integration, pytest.mark.performance]

console = Console()


async def test_get_campaigns(performance_client, save_response):
    campaigns = await performance_client.campaigns.get_campaigns()
    save_response(campaigns)
    assert isinstance(campaigns, list)


async def test_get_campaign_by_id(performance_client, save_response):
    campaigns = await performance_client.campaigns.get_campaigns()
    if not campaigns:
        pytest.skip("No campaigns found in account")

    campaign_id = str(campaigns[0]["id"])
    result = await performance_client.campaigns.get_campaign_by_id(campaign_id)
    save_response(result)
    assert isinstance(result, dict)


async def test_get_statistics_report(performance_client, save_response):
    campaigns = await performance_client.campaigns.get_campaigns()
    if not campaigns:
        pytest.skip("No campaigns found in account")

    campaign_id = str(campaigns[0]["id"])
    date_to = datetime.now()
    date_from = date_to - timedelta(days=7)

    def on_progress(progress: ReportPollingProgress):
        """Display polling progress in real-time with rich formatting."""
        status_color = "yellow" if progress.status != "OK" else "green"

        console.print(
            f"[cyan][[/cyan][bold cyan]{progress.attempt}/{progress.max_attempts}[/bold cyan][cyan]][/cyan] "
            f"[dim]UUID:[/dim] [magenta]{progress.report_uuid[:8]}...[/magenta] "
            f"[dim]|[/dim] Status: [{status_color}]{progress.status or 'UNKNOWN'}[/{status_color}] "
            f"[dim]|[/dim] ⏱️  [blue]{progress.elapsed_seconds:.1f}s[/blue] "
            f"[dim]|[/dim] Progress: [green]{progress.progress_percent:.0f}%[/green]"
        )

        if progress.next_poll_in:
            console.print(f"  [dim]→ Next poll in {progress.next_poll_in:.1f}s...[/dim]")

    console.rule("[bold blue]Statistics Report Test[/bold blue]")
    console.print(f"📊 [bold]Campaign ID:[/bold] [cyan]{campaign_id}[/cyan]")
    console.print(f"📅 [bold]Period:[/bold] [yellow]{date_from.date()}[/yellow] to [yellow]{date_to.date()}[/yellow]")
    console.print()

    result = await performance_client.campaigns.get_statistics_report(
        campaign_ids=[campaign_id],
        date_from=date_from,
        date_to=date_to,
        max_attempts=10,
        poll_interval=5.0,
        on_progress=on_progress,
    )

    console.print()
    console.print("✅ [bold green]Report ready![/bold green]")

    # Отобразить информацию о полученном отчете
    console.print(f"📊 [bold]Campaigns:[/bold] [cyan]{len(result)}[/cyan]")

    for campaign in result:
        campaign_id = campaign["campaign_id"]
        console.print(f"\n[bold cyan]Campaign {campaign_id}:[/bold cyan]")
        console.print(f"  [dim]Header:[/dim] {campaign['campaign_header'][:80]}...")
        console.print(f"  [bold]Rows:[/bold] [yellow]{len(campaign['data'])}[/yellow]")

        # Показать первые 3 строки данных
        if campaign["data"]:
            console.print("  [dim]Sample data:[/dim]")
            for row in campaign["data"][:3]:
                sku = row.get("sku", "N/A")
                shows = row.get("Показы", "0")
                clicks = row.get("Клики", "0")
                console.print(f"    SKU: [cyan]{sku}[/cyan], Показы: {shows}, Клики: {clicks}")

    console.rule()
    save_response(result)
    assert isinstance(result, list)
    assert len(result) > 0
    assert all("campaign_id" in c and "data" in c for c in result)
