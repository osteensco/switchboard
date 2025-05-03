from .cloud import Cloud



class Invoke():
    def __init__(self, body: str, cloud: Cloud) -> None:
        self._cloud = cloud
        
    def dosomething(self):
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



