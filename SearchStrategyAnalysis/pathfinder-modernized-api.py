"""
FastAPI REST API for Pathfinder Morris Water Maze Analysis.
Provides programmatic access to analysis functions.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

from pathfinder_modernized_models import (
    Experiment, Trial, Parameters, Datapoint, SearchStrategy, AnalysisResult
)
from pathfinder_modernized_analysis import StrategyAnalyzer


# Initialize FastAPI app
app = FastAPI(
    title="Pathfinder API",
    description="Morris Water Maze search strategy analysis API",
    version="2.0.0"
)

# In-memory storage (replace with database in production)
experiments_db: dict[str, Experiment] = {}
analysis_results_db: dict[str, List[AnalysisResult]] = {}


# ============================================================================
# Request/Response Schemas
# ============================================================================

class TrialRequest(BaseModel):
    """Request schema for trial data"""
    trial_number: int
    day: int
    trajectory: List[dict]  # [{x, y, time}, ...]
    platform_position: tuple[float, float]
    platform_diameter: float
    pool_center: tuple[float, float]
    pool_diameter: float


class ExperimentRequest(BaseModel):
    """Request schema for experiment creation"""
    experiment_name: str
    researcher: Optional[str] = None
    tracking_software: str
    parameters: Optional[dict] = None
    trials: Optional[List[TrialRequest]] = None


class AnalysisRequest(BaseModel):
    """Request schema for analysis"""
    experiment_id: str
    use_manual_categorization: bool = False


class AnalysisResponse(BaseModel):
    """Response schema for analysis results"""
    experiment_id: str
    results_count: int
    timestamp: datetime
    strategies_detected: dict[str, int]  # Count by strategy
    average_confidence: float


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


@app.post("/experiments", response_model=dict)
async def create_experiment(request: ExperimentRequest):
    """
    Create a new experiment.
    
    Args:
        request: Experiment configuration
        
    Returns:
        Created experiment with ID
    """
    experiment_id = str(uuid.uuid4())
    
    # Use provided parameters or defaults
    params = Parameters(**request.parameters) if request.parameters else Parameters()
    
    # Parse trials
    trials: List[Trial] = []
    if request.trials:
        for trial_req in request.trials:
            trajectory = [
                Datapoint(**dp) for dp in trial_req.trajectory
            ]
            trial = Trial(
                trial_id=f"{experiment_id}_trial_{trial_req.trial_number}",
                trial_number=trial_req.trial_number,
                day=trial_req.day,
                trajectory=trajectory,
                platform_position=trial_req.platform_position,
                platform_diameter=trial_req.platform_diameter,
                pool_center=trial_req.pool_center,
                pool_diameter=trial_req.pool_diameter
            )
            trials.append(trial)
    
    # Create experiment
    experiment = Experiment(
        experiment_id=experiment_id,
        experiment_name=request.experiment_name,
        researcher=request.researcher,
        parameters=params,
        trials=trials,
        tracking_software=request.tracking_software
    )
    
    # Store in database
    experiments_db[experiment_id] = experiment
    
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment.experiment_name,
        "trials_count": len(trials),
        "created_at": experiment.created_at
    }


@app.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """
    Retrieve experiment details.
    
    Args:
        experiment_id: ID of experiment
        
    Returns:
        Experiment data
        
    Raises:
        HTTPException: If experiment not found
    """
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments_db[experiment_id]
    
    return {
        "experiment_id": experiment.experiment_id,
        "experiment_name": experiment.experiment_name,
        "researcher": experiment.researcher,
        "tracking_software": experiment.tracking_software,
        "trials_count": len(experiment.trials),
        "created_at": experiment.created_at,
        "parameters": experiment.parameters.model_dump()
    }


@app.post("/experiments/{experiment_id}/analyze")
async def analyze_experiment(
    experiment_id: str,
    background_tasks: BackgroundTasks,
    request: AnalysisRequest
):
    """
    Run analysis on an experiment.
    
    Args:
        experiment_id: ID of experiment to analyze
        background_tasks: FastAPI background tasks
        request: Analysis configuration
        
    Returns:
        Analysis results summary
        
    Raises:
        HTTPException: If experiment not found
    """
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments_db[experiment_id]
    
    # Run analysis
    analyzer = StrategyAnalyzer(experiment.parameters)
    results: List[AnalysisResult] = []
    confidence_scores: List[float] = []
    strategy_counts: dict[str, int] = {}
    
    for trial in experiment.trials:
        strategy, confidence = analyzer.analyze_trial(trial)
        
        result = AnalysisResult(
            experiment_id=experiment_id,
            trial_id=trial.trial_id,
            detected_strategy=strategy,
            confidence=confidence,
            metrics=analyzer._calculate_metrics(trial)
        )
        results.append(result)
        confidence_scores.append(confidence)
        
        strategy_name = strategy.value
        strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
    
    # Store results
    analysis_results_db[experiment_id] = results
    
    # Update trials with detected strategies
    for i, result in enumerate(results):
        experiment.trials[i].search_strategy = result.detected_strategy
    
    # Calculate summary
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    return {
        "experiment_id": experiment_id,
        "results_count": len(results),
        "timestamp": datetime.now(),
        "strategies_detected": strategy_counts,
        "average_confidence": avg_confidence
    }


@app.get("/experiments/{experiment_id}/results")
async def get_analysis_results(experiment_id: str):
    """
    Retrieve analysis results for an experiment.
    
    Args:
        experiment_id: ID of experiment
        
    Returns:
        List of analysis results
        
    Raises:
        HTTPException: If results not found
    """
    if experiment_id not in analysis_results_db:
        raise HTTPException(status_code=404, detail="Analysis results not found")
    
    results = analysis_results_db[experiment_id]
    
    return {
        "experiment_id": experiment_id,
        "results": [r.model_dump() for r in results],
        "count": len(results)
    }


@app.get("/experiments/{experiment_id}/summary")
async def get_experiment_summary(experiment_id: str):
    """
    Get summary statistics for experiment.
    
    Args:
        experiment_id: ID of experiment
        
    Returns:
        Summary statistics
    """
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments_db[experiment_id]
    
    # Calculate statistics
    escape_latencies = [
        t.escape_latency for t in experiment.trials 
        if t.escape_latency is not None
    ]
    path_lengths = [
        t.path_length for t in experiment.trials 
        if t.path_length is not None
    ]
    
    strategy_counts = {}
    for trial in experiment.trials:
        if trial.search_strategy:
            s = trial.search_strategy.value
            strategy_counts[s] = strategy_counts.get(s, 0) + 1
    
    return {
        "experiment_id": experiment_id,
        "trials_analyzed": len(experiment.trials),
        "average_escape_latency": sum(escape_latencies) / len(escape_latencies) if escape_latencies else None,
        "average_path_length": sum(path_lengths) / len(path_lengths) if path_lengths else None,
        "strategy_distribution": strategy_counts
    }


@app.get("/experiments")
async def list_experiments(limit: int = 10, offset: int = 0):
    """
    List all experiments.
    
    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of experiment summaries
    """
    experiments = list(experiments_db.values())[offset:offset + limit]
    
    return {
        "total": len(experiments_db),
        "limit": limit,
        "offset": offset,
        "experiments": [
            {
                "experiment_id": e.experiment_id,
                "experiment_name": e.experiment_name,
                "trials_count": len(e.trials),
                "created_at": e.created_at
            }
            for e in experiments
        ]
    }


# ============================================================================
# Error Handling
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
