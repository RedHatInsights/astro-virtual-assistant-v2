import pathlib

_base = pathlib.Path(__file__).parent.resolve().joinpath("resources")


async def async_value(value):
    return value


def path_to_resource(resource):
    return str(_base.joinpath(resource))
