To start development

1. install uv cli utility 
https://github.com/astral-sh/uv

2. run ```uv sync --frozen``` in the agent-runner directory (same as this readme)

4. to upgrade project dependencies, run  ```uv lock --upgrade``` or ```uv lock --upgrade <package>```

5. to run the project http api, use ```uv run fastapi dev src/tool_executor/app.py```