run_lb:
	poetry run uvicorn src.load_balancer.load_balancer:load_balancer --port 8080

run_client:
	poetry run python -m src.client.client