Требование создать систему распознавания файлов, документов и интеграция с 1С. Это будет веб интерфейс на FastAPI + jinja шаблонизатор. На странице кнопка загрузить файл. Загружается картинка, она распознается через LLM. И затем информация из этой страницы отправляется в 1С через Api odata.

Также должна быть страница с настройками:
- адрес 1С, логин и пароль
- LLM: название модели, url api, пароль.

Будут распознаваться разные документы, поэтому первое нужно определить тип документа, затем для этого документа собрать список tools. Когда распознается картинка вызывается этот список tools, Например add_row(название, код, товар, кол-ов, цена). LLM должна прочитать картинку и вызывать эти tools. После этого вернуть результат в json,

Пример загрузки картинки в LLM

```

from pydantic_ai import Agent, ImageUrl, RunContext
from pydantic_ai.capabilities import AbstractCapability

class Recognize():
    
    def __init__(self):
        self.lines = []
    
    def add(self, name, value):
        self.lines.append({
            "name": name,
            "value": value,
        })
    

def tool_example(ctx: RunContext, name: str, value: str):
    ctx.deps.add(name, value)
    return "Message"

class Parser(AbstractCapability):
    
    def get_toolset():
        return FunctionToolset(tools=[tool_example])

def build_agent(name, capabilities):
    agent = Agent(
        name,
        capabilities=capabilities
    )
    return agent

async def run(agent, image):
    result = await agent.run(
        [
            user_message,
            BinaryContent(data=image_response.content, media_type='image/png)
        ],
        deps=Recognize()
    )
    return result.output

```