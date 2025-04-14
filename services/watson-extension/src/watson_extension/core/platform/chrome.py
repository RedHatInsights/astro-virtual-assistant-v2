import injector

from watson_extension.clients.platform.chrome import ChromeServiceClient


class ChromeServiceCore:
    def __init__(self, chrome_service_client: injector.Inject[ChromeServiceClient]):
        self.chrome_service_client = chrome_service_client
    
    async def get_service_options(self):
        services = await self.chrome_service_client.get_generated_services()
        parsed = parse_generated_services(services)
        options = []
        for s in parsed:
            if "href" in s:
                options.append(convert_service_to_option(s))
        
        return options
    
    async def get_user(self):
        return await self.chrome_service_client.get_user()
    
    async def _get_service_by_title(self, title):
        # get all services, find the href
        service = None
        services = await self.chrome_service_client.get_generated_services()
        parsed = parse_generated_services(services)
        print(f"Parsed services: {parsed}")
        for s in parsed:
            if title.lower() == s["title"].lower() or title.lower() in (t.lower() for t in s["alt_title"]):
                service = s
                break
        
        return service
    
    async def _is_favorited(self, href):
        user = await self.get_user()
        if not user.favorite_pages:
            return False
        favorites = user.favorite_pages
        for favorite in favorites:
            if favorite.pathname == href:
                return True
        return False

    async def get_service_data(self, title):
        service = await self._get_service_by_title(title)
        if not service:
            return None

        href = service["href"]
        favorited_already = await self._is_favorited(href)

        return {
            "service": service["title"],
            "link": href,
            "group": service["group"],
            "already": favorited_already
        }
        
    async def modify_favorite_service(self, href, favorite):
        await self.chrome_service_client.modify_favorite_service(href=href, favorite=favorite)

# Helpers
def parse_generated_services(content):
    print("content", content)
    services = []
    for category in content:
        for link in category["links"]:
            group_title = link.get("title")
            if "isGroup" in link and link["isGroup"]:
                for sublink in link["links"]:
                    if "isExternal" in sublink and sublink["isExternal"]:
                        # not really a service
                        continue
                    service = {"group": group_title}

                    if "href" in sublink:
                        service["href"] = sublink["href"]
                    if "title" in sublink:
                        service["title"] = sublink["title"]
                    if "appId" in sublink:
                        service["app_id"] = sublink["appId"]
                    service["alt_title"] = sublink.get("alt_title", [])
                    services.append(service)
    return services

def convert_service_to_option(service):
    value = {"group": service["group"]}
    synonyms = [service["href"]]
    value["href"] = service["href"]

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