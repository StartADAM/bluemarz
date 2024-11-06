# Session

# Properties

| Attribute | Type        | Description  |
|-----------|-------------|--------------|
| spec      | SessionSpec | Session spec |
|           |             |              |

# Methods

## from_spec

def from_spec(cls, spec: models.SessionSpec) -> "Session":

Create a Session from spec.

| Parameter | Type        | Description  |
|-----------|-------------|--------------|
| spec      | SessionSpec | Session spec |
|           |             |              |

**returns** Session

## delete_session

def delete_session(self) -> models.DeleteSessionResult:

Delete the current Session. It may have different interpretations, according to the Provider. 
The Session may be really delete, or just archived.


| Parameter | Type | Description |
|-----------|------|-------------|
| -         | -    | -           |
|           |      |             |

** returns ** DeleteSessionResult: bool

## add_message

def add_message(self, message: models.SessionMessage) -> models.AddMessageResult

Send a message to an Agent in the Session.


| Parameter | Type           | Description         |
|-----------|----------------|---------------------|
| message   | SessionMessage | message to be added |
|           |                |                     |

** returns ** AddMessageResult: bool



## add_file

def add_file(self, file: models.SessionFile) -> models.AddFileResult

Add a file to a Session, in its context window.


| Parameter | Type        | Description      |
|-----------|-------------|------------------|
| file      | SessionFile | file to be added |
|           |             |                  |

** returns ** AddFileResult: bool

