# My agent: Endurance Pulse (Fitness & Endurance Coach)

One-liner: A conversational fitness and endurance coach agent that helps athletes plan workouts, calculate personalized training zones, track workout logs, and generate motivational milestone visuals.

Tool coverage:
- Memory: Target event & date (e.g. 10K, Marathon, Triathlon), baseline fitness metrics (resting & max heart rate), weekly availability, and injury constraints across sessions.
- Tools: `log_workout` (record distance, time, RPE), `get_workout_history` (retrieve training logs), `get_workout_plan` (lookup structured workouts).
- Catalog/UI: Workout & Exercise Catalog (Intervals, Tempo, Long Run, Recovery) rendered as interactive cards and summary tables.
- Image gen: Motivational milestone visuals, achievement badges (e.g., "Peak Week Completed"), and race-day visual graphics.
- Sandbox: Python calculation of Karvonen Heart Rate Training Zones (Zones 1-5), Training Stress Score (TSS), and Riegel race pace predictions.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for training zone calculations and race pace estimations.
