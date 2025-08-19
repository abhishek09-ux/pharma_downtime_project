import asyncio
import subprocess
import sys
import time

async def run_machine_simulator(machine_id, delay=0):
    """Run a single machine simulator"""
    if delay > 0:
        await asyncio.sleep(delay)
    
    # Run sensor_client.py with specific machine ID
    env = {"MACHINE_ID": machine_id}
    process = await asyncio.create_subprocess_exec(
        sys.executable, "sensor_client.py", 
        env={**dict(os.environ), **env},
        cwd="."
    )
    await process.wait()

async def main():
    """Run multiple machine simulators"""
    machines = ["Machine1", "Machine2", "Machine3"]
    
    print("Starting multiple machine simulators...")
    print("Press Ctrl+C to stop all simulators")
    
    tasks = []
    for i, machine_id in enumerate(machines):
        # Start each machine with a slight delay
        task = asyncio.create_task(run_machine_simulator(machine_id, i * 2))
        tasks.append(task)
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nStopping all simulators...")
        for task in tasks:
            task.cancel()

if __name__ == "__main__":
    import os
    asyncio.run(main())
