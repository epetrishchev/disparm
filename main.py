import motor.motor_asyncio
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, FastAPI
from envparse import Env
from fastapi.routing import APIRoute
from starlette.requests import Request

# Определяем объект env для переменных окружения
env = Env()
# Определяем переменную окружения для обращения к БД, если такая переменная не
# будет задана, то будет использоваться значение default
MONGODB_URL = env.str(
    'MONGODB_URL', default='mongodb://localhost:27017/test_database')


async def ping() -> dict:
    """
    ping эндпоинт fastapi 

    Returns:
        dict: возвращает словарь при обращении к URL /ping
    """
    return {'Success': True}


async def mainpage() -> str:
    """
    mainpage endpoint главной страницы

    Returns:
        str: возвращает строку для тестового запуска
    """
    return 'You are on the main page!'


async def create_record(request: Request) -> dict:
    """
    create_record endpoint при обращении к которому создается запись в БД

    Args:
        request (Request): тело запроса

    Returns:
        dict: возвращает словарь (тело ответа)
    """
    # получаем клиента БД из запроса с именем БД test_database
    # Примечание: если попытатся подключится к несуществующей БД,
    # то в MongoDB она создаться автоматически
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client['test_database']
    # Вставляем в коллекцию records новую запись. Опять же,
    # если коллекции records на момент операции не существует MongoDB создаст ее автоматически
    await mongo_client.records.insert_one({'sample': 'record'})
    return {'Success': True}


async def get_records(request: Request) -> list:
    """
    get_records endpoint при обращении к которому получаем список записей из БД

    Args:
        request (Request): тело запроса

    Returns:
        list: список записей из БД
    """
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client['test_database']
    # Определяем курсор для поиска по БД (ленивый)
    # В метод find передается фильтр, если он пустой,
    # то находятся все записи в коллекции
    cursor = mongo_client.records.find({})
    result = []
    # проходимся по списку записей, длина которого 100 записей
    for document in await cursor.to_list(length=100):
        # получаем поле _id и преобразуем его в строку, иначе будет падать
        # ошибка 500 internal server, так как FastApi не умеет автоматом
        # преобразовывать тип Objectid который придет из БД
        document['_id'] = str(document['_id'])
        #добавляем строку в result
        result.append(document)
    return result

# Список роутов, каждый роут это объект APIRоute в котором идет привязка пути
# к эндпоинтам и определяется метод обращения
routes = [
    APIRoute(path='/ping', endpoint=ping, methods=['GET']),
    APIRoute(path='/', endpoint=mainpage, methods=['GET']),
    APIRoute(path='/create_record', endpoint=create_record, methods=['POST']),
    APIRoute(path='/get_records', endpoint=get_records, methods=['GET']),
]

# Создаем клиента и отдаем ему значение переменной URL подключения к БД
client = AsyncIOMotorClient(MONGODB_URL)
# Создаем приложение FastAPI
app = FastAPI()
# Присваиваем стейту наш клиент для связи с БД
app.state.mongo_client = client
# Подключаем наши роуты к приложению
app.include_router(APIRouter(routes=routes))
# Запуск приложения через uvicorn на порте 8000
if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)
