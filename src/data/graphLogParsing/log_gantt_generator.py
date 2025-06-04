# Example usage of the Log Gantt Generator
# Save the main file as log_gantt_generator.py, then run this:

from log_gantt_generator import LogGanttGenerator, VisualizationConfig, ChartStyle, create_quick_chart
import matplotlib.pyplot as plt

# Your log data (paste any similar log here)
log_data = '''
{
    "payload": {
        "event": "QUERY_OPERATION_COMPLETED",
        "operation_name": "FeedGroupNestedClients",
        "total_response_latency_ms": 818,
        "downstream_log": [
            {
                "status": 200,
                "service_name": "tokie",
                "method": "get",
                "path": "/signed/principals/current",
                "offset_ms": 2,
                "latency_ms": 20
            },
            {
                "status": 200,
                "service_name": "Agraph-svc",
                "method": "post",
                "path": "/graphql",
                "offset_ms": 32,
                "latency_ms": 780
            }
        ],
        "subgraph_downstream_log": [
            {
                "service_name": "grouper",
                "offset_ms": 83,
                "latency_ms": 15,
                "type": {
                    "method": "GET",
                    "path": "/api/v2/group/92851732480",
                    "code": 200
                }
            },
            {
                "service_name": "hydrant",
                "offset_ms": 104,
                "latency_ms": 251,
                "type": {
                    "method": "POST",
                    "path": "/api/v3/nested/networks/31234/feeds/group/92851732480",
                    "code": 200
                }
            }
        ]
    }
}
'''

# METHOD 1: Quick and simple
print("=== Method 1: Quick Chart ===")
fig = create_quick_chart(log_data)
plt.show()

# METHOD 2: More control with LogGanttGenerator
print("\n=== Method 2: Full Control ===")
generator = LogGanttGenerator()

# Analyze first
analysis = generator.analyze_log(log_data)
print(f"Services: {list(analysis['services'].keys())}")
print(f"Total time: {analysis['total_execution_time_ms']}ms")
print(f"Parallel groups: {analysis['parallel_groups_count']}")

# Generate chart
fig = generator.generate_from_text(log_data)
plt.show()

# METHOD 3: Custom configuration
print("\n=== Method 3: Custom Style ===")
config = VisualizationConfig(
    figsize=(16, 10),
    style=ChartStyle.MINIMAL,
    color_by_service=False,  # Color by event type instead
    group_parallel=True,
    show_labels=True
)

fig = generator.generate_with_config(log_data, config, "Custom Styled Chart")
plt.show()

# METHOD 4: Save to file
print("\n=== Method 4: Save Chart ===")
fig = generator.generate_from_text(log_data, "My Service Timeline")
fig.savefig("my_gantt_chart.png", dpi=300, bbox_inches='tight')
print("Chart saved as my_gantt_chart.png")
plt.close(fig)  # Close to free memory

print("\nDone! You can now paste any similar log JSON and get instant visualizations.")