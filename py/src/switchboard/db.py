from .cloud import AWS_db_connect, Cloud, GCP_db_connect, AZURE_db_connect







class DB():
    def __init__(self, cloud: Cloud) -> None:
        self._cloud = cloud
        self._conn = self._connect(cloud)

    def _connect(self, cloud):
        match cloud:
            case Cloud.AWS:
                AWS_db_connect()
            case Cloud.GCP:
                GCP_db_connect()
            case Cloud.AZURE:
                AZURE_db_connect()
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




