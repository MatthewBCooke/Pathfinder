#!/usr/bin/env python3
"""
Pathfinder CLI tool for batch processing Morris Water Maze data.
Modern command-line interface using Click.
"""

import click
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from pathfinder_modernized_models import (
    Experiment, Parameters, Trial, Datapoint, SearchStrategy
)
from pathfinder_modernized_analysis import StrategyAnalyzer, FileParser


@click.group()
@click.version_option(version="2.0.0", prog_name="pathfinder")
def cli():
    """
    Pathfinder: Morris Water Maze Search Strategy Analysis Tool
    
    Modern Python CLI for automated analysis of spatial navigation data.
    """
    pass


@cli.command()
@click.option(
    '--input', '-i',
    type=click.Path(exists=True),
    required=True,
    help='Input data file or directory'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='pathfinder_results.csv',
    help='Output results file'
)
@click.option(
    '--software', '-s',
    type=click.Choice(['ethovision', 'anymaze', 'watermaze', 'eztrack']),
    default='ethovision',
    help='Tracking software format'
)
@click.option(
    '--parameters', '-p',
    type=click.Path(exists=True),
    help='Custom parameters JSON file'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Verbose output'
)
def analyze(
    input: str,
    output: str,
    software: str,
    parameters: Optional[str],
    verbose: bool
):
    """
    Analyze Morris Water Maze trial data.
    
    Detects search strategies and generates results CSV.
    """
    click.echo(f"🔍 Analyzing {input}...")
    
    # Load parameters
    if parameters:
        with open(parameters) as f:
            params_dict = json.load(f)
        params = Parameters(**params_dict)
        if verbose:
            click.echo(f"📋 Loaded parameters from {parameters}")
    else:
        params = Parameters()
        if verbose:
            click.echo("📋 Using default parameters")
    
    # Parse files
    parser = FileParser(software)
    input_path = Path(input)
    
    all_trials: list[Trial] = []
    
    if input_path.is_dir():
        click.echo(f"📁 Processing directory: {input}")
        for file in input_path.glob('*'):
            if file.is_file() and file.suffix in ['.csv', '.xlsx']:
                if verbose:
                    click.echo(f"  📄 Parsing {file.name}...")
                try:
                    trials = parser.parse_file(str(file))
                    all_trials.extend(trials)
                except Exception as e:
                    click.echo(f"  ⚠️  Error parsing {file.name}: {e}")
    else:
        if verbose:
            click.echo(f"📄 Parsing single file: {input}")
        all_trials = parser.parse_file(input)
    
    click.echo(f"✅ Parsed {len(all_trials)} trials")
    
    # Analyze
    analyzer = StrategyAnalyzer(params)
    results = []
    
    with click.progressbar(
        all_trials,
        label='Analyzing trials',
        show_pos=True
    ) as bar:
        for trial in bar:
            strategy, confidence = analyzer.analyze_trial(trial)
            results.append({
                'trial_id': trial.trial_id,
                'trial_number': trial.trial_number,
                'day': trial.day,
                'strategy': strategy.value,
                'confidence': f"{confidence:.3f}",
                'escape_latency': trial.escape_latency,
                'path_length': trial.path_length
            })
    
    # Save results
    _save_results_csv(results, output)
    click.echo(f"✅ Results saved to {output}")
    
    # Print summary
    strategies_count = {}
    for r in results:
        s = r['strategy']
        strategies_count[s] = strategies_count.get(s, 0) + 1
    
    click.echo("\n📊 Summary:")
    for strategy, count in sorted(strategies_count.items()):
        click.echo(f"  {strategy}: {count}")


@cli.command()
@click.option(
    '--experiment-name', '-n',
    required=True,
    help='Name for the experiment'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='experiment.json',
    help='Output JSON file'
)
def create(experiment_name: str, output: str):
    """
    Create a new experiment configuration.
    
    Generates a template JSON file for organizing trial data.
    """
    exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    experiment_template = {
        "experiment_id": exp_id,
        "experiment_name": experiment_name,
        "researcher": "Your Name",
        "tracking_software": "ethovision",
        "created_at": datetime.now().isoformat(),
        "parameters": {
            "name": "Default",
            "ipe_max_val": 125,
            "scale_values": True
        },
        "trials": []
    }
    
    with open(output, 'w') as f:
        json.dump(experiment_template, f, indent=2)
    
    click.echo(f"✅ Created experiment template: {output}")
    click.echo(f"   Experiment ID: {exp_id}")


@cli.command()
@click.option(
    '--software', '-s',
    type=click.Choice(['ethovision', 'anymaze', 'watermaze', 'eztrack']),
    help='Tracking software to generate template for'
)
def template(software: Optional[str]):
    """
    Display or generate data import templates.
    
    Helps understand data format requirements for various tracking software.
    """
    templates = {
        'ethovision': {
            'format': 'Excel (.xlsx)',
            'columns': ['Arena', 'X center', 'Y center', 'Time'],
            'example': 'See Ethovision export documentation'
        },
        'anymaze': {
            'format': 'CSV',
            'columns': ['X', 'Y', 'Time'],
            'example': 'Anymaze export as CSV'
        },
        'watermaze': {
            'format': 'CSV',
            'columns': ['X', 'Y', 'Time'],
            'example': 'WaterMaze software export'
        },
        'eztrack': {
            'format': 'CSV',
            'columns': ['X', 'Y', 'Time'],
            'example': 'ezTrack software export'
        }
    }
    
    if software:
        info = templates.get(software)
        if info:
            click.echo(f"\n📋 {software.upper()} Format:")
            click.echo(f"   Format: {info['format']}")
            click.echo(f"   Columns: {', '.join(info['columns'])}")
            click.echo(f"   {info['example']}")
    else:
        click.echo("\n📋 Available templates:")
        for sw in templates:
            click.echo(f"   {sw}")
        click.echo("\nRun: pathfinder template -s <software> for details")


@cli.command()
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='default_parameters.json',
    help='Output parameters file'
)
def parameters(output: str):
    """
    Export default parameters as JSON.
    
    Allows customization of analysis parameters.
    """
    params = Parameters()
    params_dict = params.model_dump()
    
    with open(output, 'w') as f:
        json.dump(params_dict, f, indent=2)
    
    click.echo(f"✅ Exported parameters to {output}")
    click.echo(f"   Edit this file and use with: pathfinder analyze -p {output}")


def _save_results_csv(results: list[dict], filepath: str):
    """Save results to CSV file"""
    import csv
    
    if not results:
        return
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)


if __name__ == '__main__':
    cli()
