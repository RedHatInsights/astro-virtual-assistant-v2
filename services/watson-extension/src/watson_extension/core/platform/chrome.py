from typing import List
import injector

from watson_extension.clients.platform.chrome import ChromeServiceClient


class ChromeServiceCore:
    def __init__(self, chrome_service_client: injector.Inject[ChromeServiceClient]):
        self.chrome_service_client = chrome_service_client
    
    async def get_favorite_options(self, favoriting=True):
        user = await self.chrome_service_client.get_user()
        services = await self.chrome_service_client.get_generated_services()
        
        #if a user is requesting to remove a service, return info on the services they have favorited
        # if they are requesting to add one, return the opposite
        if not user.favorite_pages:
            return self._get_all_service_info(services)
        
        return (
            self._get_non_favorited_services_info(self, services, user.favorite_pages) if favoriting
            else self._get_favorited_services_info(self, services, user.favorite_pages)
        )
    
    def _get_all_service_info(self, services) -> List[dict]:
        return [{
                "title": service.title,
                "href": service.href,
            } for service in services]
    
    def _get_non_favorited_services_info(self, services, favorite_pages) -> List[dict]:
        return [{
            "title": service.title,
            "href": service.href,
        } for service in services if service.href not in {fav.pathname for fav in favorite_pages}]

    def _get_favorited_services_info(self, services, favorite_pages) -> List[dict]:
        return  [{
            "title": self._get_service_by_title(fav.pathname),
            "href": fav.pathname,
        } for fav in favorite_pages]

    async def get_service_options(self):
        services = await self.chrome_service_client.get_generated_services()
        parsed = parse_generated_services(services)
        options = []
        for s in parsed:
            if s.get("href", ""):
                options.append(convert_service_to_option(s))

        return options

    async def get_user(self):
        return await self.chrome_service_client.get_user()

    async def _get_service_by_title(self, title):
        def is_synonym(service):
            return title.lower() in (t.lower() for t in service["synonyms"])

        options = await self.get_service_options()
        service = next((s for s in options if is_synonym(s)), None)

        return service["data"] if service else None

    async def _is_favorited(self, href):
        user = await self.get_user()
        if not user.favorite_pages:
            return False
        favorites = user.favorite_pages
        return any(favorite.pathname == href for favorite in favorites)

    async def get_service_data(self, title):
        service = await self._get_service_by_title(title)
        if not service:
            return None

        href = service["href"]
        favorited_already = await self._is_favorited(href)

        return {
            "service": service["title"],
            "href": href,
            "group": service["group"],
            "already": favorited_already,
        }

    async def modify_favorite_service(self, href, favorite):
        return await self.chrome_service_client.modify_favorite_service(
            href=href, favorite=favorite
        )


# Helpers
def parse_generated_services(content):
    services = []
    for category in content:
        for link in category.links:
            group_title = link.title
            if link.is_group:
                for sublink in link.links:
                    if sublink.is_external:
                        # not really a service
                        continue
                    service = {"group": group_title}

                    if sublink.href:
                        service["href"] = sublink.href
                    if sublink.title:
                        service["title"] = sublink.title
                    if sublink.app_id:
                        service["app_id"] = sublink.app_id
                    service["alt_title"] = sublink.alt_title
                    services.append(service)
    return services


def convert_service_to_option(service):
    value = {"group": service.get("group", "")}
    synonyms = [service.get("href", "")]
    value["href"] = service.get("href", "")

    if "title" in service:
        value["title"] = service["title"]
        synonyms.append(service["title"])
    if "appId" in service:
        value["app_id"] = service["appId"]
        synonyms.append(service["appId"])
    if "alt_title" in service:
        synonyms += service["alt_title"]
    return {
        "data": value,
        "synonyms": synonyms,
    }
