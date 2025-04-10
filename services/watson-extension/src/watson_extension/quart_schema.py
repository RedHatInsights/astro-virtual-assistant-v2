from typing import Dict, Any, Tuple, List, Type, Optional, Iterable

from quart_schema import DataSource, OpenAPIProvider
from quart_schema.openapi import Model, Rule


# Given the requirements [1] for a watson extension, we cannot use openapi 3.1.0 or anyOf, oneOf, allOf, among other things.
# We will have to patch them or maintain manually the API for the watson-extension.
# We can try to patch the openapi file as long as we can.
#
# [1] https://cloud.ibm.com/docs/watson-assistant/watson-assistant?topic=watson-assistant-build-custom-extension
class WatsonExtensionAPIProvider(OpenAPIProvider):
    def schema(self) -> Dict[str, Any]:
        schema = super().schema()
        schema["openapi"] = "3.0.0"
        return schema

    def generate_rules(self) -> Iterable[Rule]:
        for rule in super().generate_rules():
            # This static endpoints gets added when using quart-injector - unsure if it's a dev only rule, but hiding from here.
            if rule.endpoint == "static":
                continue

            yield rule

    def build_paths(self, rule: Rule) -> Tuple[dict, dict]:
        paths, components = super().build_paths(rule)

        if rule.endpoint.startswith("public_root_alias"):
            return dict(), dict()

        for component in components.values():
            self._patch_schema(component)

        for path in paths.values():
            for method_name in path:
                method = path[method_name]
                method["operationId"] = f"{method_name.lower()}_{rule.endpoint}"

        return paths, components

    def build_querystring_parameters(
        self, model: Type[Model]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        parameters, definitions = super().build_querystring_parameters(model)
        for parameter in parameters:
            if "schema" in parameter:
                self._patch_schema(parameter["schema"])
        return parameters, definitions

    def build_request_body(
        self, model: Type[Model], source: DataSource
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        request_body, definitions = super().build_request_body(model, source)
        if "content" in request_body:
            content = request_body["content"]
            for content_type in content:
                if "schema" in content[content_type]:
                    self._patch_schema(content[content_type]["schema"])

        return request_body, definitions

    def build_response_object(
        self, model: Type[Model], headers_model: Optional[Type[Model]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        response, definitions = super().build_response_object(model, headers_model)
        if "content" in response:
            content = response["content"]
            for content_type in content:
                if "schema" in content[content_type]:
                    self._patch_schema(content[content_type]["schema"])
        return response, definitions

    def _patch_schema(self, schema: Dict[str, Any]):
        if schema.get("type", "") == "object":
            for property_key in schema.get("properties", []):
                prop = schema.get("properties")[property_key]
                self._patch_schema(prop)

        if "anyOf" in schema:
            schema["anyOf"] = [
                v for v in schema["anyOf"] if not self._is_type_with_null_string(v)
            ]
            if len(schema["anyOf"]) == 1:
                content = schema["anyOf"][0]
                if set(content.keys()).isdisjoint(schema):
                    if "default" in schema:
                        del schema["default"]

                    for content_key in content:
                        schema[content_key] = content[content_key]
                    schema["anyOf"] = []

            if len(schema["anyOf"]) == 0:
                del schema["anyOf"]

        if "const" in schema:
            if "enum" not in schema:
                schema["enum"] = [schema["const"]]
            del schema["const"]

    def _is_type_with_null_string(self, value: dict[str, Any]) -> bool:
        return len(value) == 1 and "type" in value and value["type"] == "null"
