"""Command-line interface."""

from __future__ import annotations

import statistics

import click

from llm_integration_starter.client import UnifiedLLMClient
from llm_integration_starter.fallback import FallbackChain


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """LLM Integration Starter Kit CLI."""
    pass


@cli.command()
@click.option("--provider", default="mock", help="Provider name")
@click.option("--model", default=None, help="Model name")
@click.option("--temperature", default=0.7, help="Temperature")
@click.argument("message")
def chat(provider: str, model: str | None, temperature: float, message: str):
    """Send a single message."""
    try:
        client = UnifiedLLMClient(provider=provider, model=model)
        messages = [{"role": "user", "content": message}]
        click.echo(f"Sending to {provider}...", err=True)
        response = client.complete(messages, temperature=temperature)
        click.echo("\nResponse:")
        click.echo(response.text)
        click.echo("\nMetadata:", err=True)
        click.echo(f"  Tokens: {response.input_tokens} in, {response.output_tokens} out", err=True)
        click.echo(f"  Cost: ${response.cost:.4f}", err=True)
        click.echo(f"  Latency: {response.latency_ms:.0f}ms", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--providers", default="mock", help="Comma-separated providers")
@click.option("--temperature", default=0.7, help="Temperature")
@click.argument("message")
def compare(providers: str, temperature: float, message: str):
    """Compare responses from multiple providers."""
    provider_list = [p.strip() for p in providers.split(",")]
    messages = [{"role": "user", "content": message}]
    click.echo(f"Comparing {len(provider_list)} providers...\n", err=True)
    for provider_name in provider_list:
        try:
            client = UnifiedLLMClient(provider=provider_name)
            response = client.complete(messages, temperature=temperature)
            click.echo(f"{'=' * 60}")
            click.echo(f"Provider: {provider_name}")
            click.echo(f"{'=' * 60}")
            click.echo(response.text)
            click.echo(f"\nTokens: {response.input_tokens} in, {response.output_tokens} out")
            click.echo(f"Cost: ${response.cost:.4f}")
            click.echo(f"Latency: {response.latency_ms:.0f}ms")
            click.echo()
        except Exception as e:
            click.echo(f"Error with {provider_name}: {e}", err=True)
            click.echo()


@cli.command()
@click.option("--provider", default="mock", help="Provider name")
@click.option("--n-requests", default=10, help="Number of requests")
@click.option("--temperature", default=0.7, help="Temperature")
@click.argument("message", default="Hello")
def benchmark(provider: str, n_requests: int, temperature: float, message: str):
    """Benchmark provider performance."""
    click.echo(f"Benchmarking {provider} with {n_requests} requests...\n", err=True)
    client = UnifiedLLMClient(provider=provider)
    messages = [{"role": "user", "content": message}]
    latencies = []
    costs = []
    total_tokens = 0
    with click.progressbar(range(n_requests), label="Running requests") as bar:
        for _ in bar:
            try:
                response = client.complete(messages, temperature=temperature)
                latencies.append(response.latency_ms)
                costs.append(response.cost)
                total_tokens += response.input_tokens + response.output_tokens
            except Exception as e:
                click.echo(f"\nError: {e}", err=True)
    if latencies:
        click.echo("\nResults:")
        click.echo(f"  Successful requests: {len(latencies)}/{n_requests}")
        click.echo("  Latency:")
        click.echo(f"    Mean: {statistics.mean(latencies):.0f}ms")
        click.echo(f"    Median: {statistics.median(latencies):.0f}ms")
        if len(latencies) > 1:
            click.echo(f"    StdDev: {statistics.stdev(latencies):.0f}ms")
        click.echo(f"    Min: {min(latencies):.0f}ms")
        click.echo(f"    Max: {max(latencies):.0f}ms")
        click.echo("  Cost:")
        click.echo(f"    Total: ${sum(costs):.4f}")
        click.echo(f"    Per request: ${statistics.mean(costs):.4f}")
        click.echo(f"  Tokens: {total_tokens}")
    else:
        click.echo("\nNo successful requests", err=True)


@cli.command()
@click.option("--providers", default="mock", help="Comma-separated providers")
@click.option("--temperature", default=0.7, help="Temperature")
@click.argument("message")
def fallback(providers: str, temperature: float, message: str):
    """Test fallback chain."""
    provider_list = [p.strip() for p in providers.split(",")]
    messages = [{"role": "user", "content": message}]
    click.echo(f"Testing fallback chain: {' → '.join(provider_list)}\n", err=True)
    try:
        chain = FallbackChain(providers=provider_list)
        result = chain.execute(messages, temperature=temperature)
        click.echo("Success!")
        click.echo(f"  Successful provider: {result.successful_provider}")
        click.echo(f"  Attempts: {result.attempts}")
        if result.errors:
            click.echo("  Errors from failed attempts:")
            for error in result.errors:
                click.echo(f"    - {error}")
        click.echo("\nResponse:")
        click.echo(result.response.text)
    except Exception as e:
        click.echo(f"All providers failed: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
