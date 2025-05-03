from enum import Enum





def AWS_connect():
    pass

def GCP_connect():
    pass

def AZURE_connect():
    pass



class Cloud(Enum):
    AWS = 'AWS'
    GCP = 'GCP'
    AZURE = 'AZURE'



class DB():
    def __init__(self, cloud: Cloud) -> None:
        self._cloud = cloud
        self._conn = self._connect(cloud)

    def _connect(self, cloud):
        match cloud:
            case Cloud.AWS:
                AWS_connect()
            case Cloud.GCP:
                GCP_connect()
            case Cloud.AZURE:
                AZURE_connect()
            case _:
                raise ValueError
        return


    def read(self):
        match self._cloud:
            case Cloud.AWS:
                pass
            case Cloud.GCP:
                pass
            case Cloud.AZURE:
                pass
            case _:
                raise ValueError
        return


    def write(self):
        match self._cloud:
            case Cloud.AWS:
                pass
            case Cloud.GCP:
                pass
            case Cloud.AZURE:
                pass
            case _:
                raise ValueError
        return

    def increment_id(self):
        pass




