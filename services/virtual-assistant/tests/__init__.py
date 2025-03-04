import pathlib

_base = pathlib.Path(__file__).parent.resolve().joinpath("resources")


async def async_value(value):
    return value


def path_to_resource(resource):
    return str(_base.joinpath(resource))


def get_resource_contents(resource):
    path = path_to_resource(resource)
    buff = []
    with open(path, "r") as f:
        for line in f:
            buff.append(line)

    return "".join(buff)
