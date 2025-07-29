from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from sqlmodel import SQLModel, create_engine, Session, Field
from datetime import datetime, UTC

app = FastAPI()

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


class WebsocketMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    datetime: datetime
    user_id: int


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
            
            const second = 1000;
            const minute = second * 60;
            const intervalID = setInterval(myCallback, minute);

            function myCallback() {
                ws.send("Track time")
            };
            
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:

        while True:
            data = await websocket.receive_text()

            session = next(get_session())

            model_db = WebsocketMessage(datetime=datetime.now(UTC), user_id=client_id)
            session.add(model_db)
            session.commit()

            await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


# WORKS!!!
# select sum(case when age(datetime,lag) < interval '65 second' then age(datetime,lag) end) as interval from (
# 	SELECT  *, lag(w.datetime,1 )
# 	OVER(ORDER By w.datetime)
# 	as lag
# 	FROM  websocketmessage w
# 	where user_id = 5
# )
# {"minutes":24,"seconds":59,"milliseconds":998.457}


# select datetime, lag from (
# 	SELECT  *, lag(w.datetime,1 )
# 	OVER(ORDER By w.datetime)
# 	as lag
# 	FROM  websocketmessage w
# 	where user_id = 5
# )


# select datetime, lag, age(datetime,lag) from (
# 	SELECT  *, lag(w.datetime,1 )
# 	OVER(ORDER By w.datetime)
# 	as lag
# 	FROM  websocketmessage w
# 	where user_id = 5
# )


# select sum(age(datetime,lag)) from (
# 	SELECT  *, lag(w.datetime,1 )
# 	OVER(ORDER By w.datetime)
# 	as lag
# 	FROM  websocketmessage w
# 	where user_id = 5
# ) LIMIT 100
# {"minutes":26,"seconds":52,"milliseconds":999.93}


# CREATE TABLE websocketmessage(
#     id SERIAL NOT NULL,
#     datetime timestamp without time zone NOT NULL,
#     user_id integer NOT NULL,
#     PRIMARY KEY(id)
# );

# CREATE TABLE websocketmessage (
# 	id INTEGER NOT NULL,
# 	datetime timestamp without time zone NOT NULL,
# 	user_id INTEGER NOT NULL,
# 	PRIMARY KEY (id)
# );

# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 02:20:41.256000',1),
# 	 ('2025-07-29 02:20:46.792045',1),
# 	 ('2025-07-29 02:36:02.455939',2),
# 	 ('2025-07-29 02:36:03.455232',2),
# 	 ('2025-07-29 02:36:04.455818',2),
# 	 ('2025-07-29 02:36:05.455648',2),
# 	 ('2025-07-29 02:36:06.455660',2),
# 	 ('2025-07-29 02:36:07.455604',2),
# 	 ('2025-07-29 02:36:08.455949',2),
# 	 ('2025-07-29 02:36:09.456200',2);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 02:36:10.454997',2),
# 	 ('2025-07-29 02:36:11.455288',2),
# 	 ('2025-07-29 02:36:12.455934',2),
# 	 ('2025-07-29 02:36:13.455045',2),
# 	 ('2025-07-29 02:36:14.455183',2),
# 	 ('2025-07-29 02:36:15.455296',2),
# 	 ('2025-07-29 02:36:16.454927',2),
# 	 ('2025-07-29 02:36:17.455106',2),
# 	 ('2025-07-29 02:37:53.348675',3),
# 	 ('2025-07-29 02:37:57.348451',4);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 02:38:53.347881',3),
# 	 ('2025-07-29 02:38:56.962154',4),
# 	 ('2025-07-29 02:39:53.348291',3),
# 	 ('2025-07-29 02:39:56.962052',4),
# 	 ('2025-07-29 02:40:53.348142',3),
# 	 ('2025-07-29 02:40:56.961779',4),
# 	 ('2025-07-29 02:41:53.348347',3),
# 	 ('2025-07-29 02:41:56.962030',4),
# 	 ('2025-07-29 02:42:53.348259',3),
# 	 ('2025-07-29 02:42:56.961663',4);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 02:43:56.962380',4),
# 	 ('2025-07-29 02:43:59.348619',3),
# 	 ('2025-07-29 02:44:56.962387',4),
# 	 ('2025-07-29 02:44:59.349459',3),
# 	 ('2025-07-29 02:45:56.963164',4),
# 	 ('2025-07-29 02:45:59.348340',3),
# 	 ('2025-07-29 02:46:56.962331',4),
# 	 ('2025-07-29 02:46:59.347797',3),
# 	 ('2025-07-29 02:47:56.961702',4),
# 	 ('2025-07-29 02:47:59.348477',3);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 02:48:53.347735',3),
# 	 ('2025-07-29 02:48:56.962239',4),
# 	 ('2025-07-29 02:49:56.961663',4),
# 	 ('2025-07-29 02:49:59.348553',3),
# 	 ('2025-07-29 02:50:57.347864',4),
# 	 ('2025-07-29 02:50:59.349444',3),
# 	 ('2025-07-29 03:23:06.348307',5),
# 	 ('2025-07-29 03:23:11.282020',6),
# 	 ('2025-07-29 03:24:06.348119',5),
# 	 ('2025-07-29 03:24:11.282326',6);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 03:25:06.347809',5),
# 	 ('2025-07-29 03:25:11.347536',6),
# 	 ('2025-07-29 03:26:06.347595',5),
# 	 ('2025-07-29 03:26:11.347478',6),
# 	 ('2025-07-29 03:27:06.347388',5),
# 	 ('2025-07-29 03:27:11.347963',6),
# 	 ('2025-07-29 03:28:06.347588',5),
# 	 ('2025-07-29 03:28:11.347495',6),
# 	 ('2025-07-29 03:29:59.349061',5),
# 	 ('2025-07-29 03:29:59.368663',6);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 03:30:59.349184',5),
# 	 ('2025-07-29 03:30:59.355351',6),
# 	 ('2025-07-29 03:31:59.349524',5),
# 	 ('2025-07-29 03:31:59.370131',6),
# 	 ('2025-07-29 03:32:59.347812',5),
# 	 ('2025-07-29 03:32:59.366913',6),
# 	 ('2025-07-29 03:33:59.349743',5),
# 	 ('2025-07-29 03:33:59.368971',6),
# 	 ('2025-07-29 03:34:59.350128',5),
# 	 ('2025-07-29 03:34:59.355793',6);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 03:35:59.349527',5),
# 	 ('2025-07-29 03:35:59.368385',6),
# 	 ('2025-07-29 03:36:59.349549',5),
# 	 ('2025-07-29 03:36:59.355749',6),
# 	 ('2025-07-29 03:37:59.348833',5),
# 	 ('2025-07-29 03:37:59.353673',6),
# 	 ('2025-07-29 03:38:59.353086',5),
# 	 ('2025-07-29 03:38:59.357806',6),
# 	 ('2025-07-29 03:39:59.348483',5),
# 	 ('2025-07-29 03:39:59.367171',6);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 03:40:59.348619',5),
# 	 ('2025-07-29 03:40:59.367810',6),
# 	 ('2025-07-29 03:41:59.348465',5),
# 	 ('2025-07-29 03:41:59.367341',6),
# 	 ('2025-07-29 03:42:59.347902',5),
# 	 ('2025-07-29 03:42:59.366914',6),
# 	 ('2025-07-29 03:43:59.348025',5),
# 	 ('2025-07-29 03:43:59.353117',6),
# 	 ('2025-07-29 03:44:11.282077',6),
# 	 ('2025-07-29 03:44:59.348562',5);
# INSERT INTO websocketmessage (datetime,user_id) VALUES
# 	 ('2025-07-29 03:45:11.282363',6),
# 	 ('2025-07-29 03:45:59.348903',5),
# 	 ('2025-07-29 03:46:11.347659',6),
# 	 ('2025-07-29 03:46:59.348775',5),
# 	 ('2025-07-29 03:47:59.348938',5),
# 	 ('2025-07-29 03:47:59.354190',6),
# 	 ('2025-07-29 03:48:59.349030',5),
# 	 ('2025-07-29 03:48:59.354494',6),
# 	 ('2025-07-29 03:49:59.348237',5),
# 	 ('2025-07-29 03:49:59.367505',6);
