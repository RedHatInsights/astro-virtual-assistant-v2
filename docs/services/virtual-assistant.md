# Virtual assistant

This is the main REST API for virtual assistant. It listens for calls from users of the platform and routes the
requests to watson and returns the contents of the "conversation" to the user.

See more info at our [documentation](/docs/services/virtual-assistant.md)

# Class Diagram

![Class Diagram](/docs/diagrams/virtual-assistant-class.mermaid)

## RHEL Lightspeed

![RHEL Lightspeed sequence diagram](/docs/diagrams/virtual-assistant-rhel-lightspeed-sequence.mermaid)

## Running locally
This service can be run by using `make run` from the root of the project. It will start the service
listening on port 5000.

API spec is [served](http://127.0.0.1:5000/api/virtual-assistant-watson-extension/v2/openapi.json) by the service.
There are also [redocs](http://127.0.0.1:5000/redocs), [scalar](http://127.0.0.1:5000/scalar) and [swagger](http://127.0.0.1:5000/docs) frontends available for convenience.

If access to services within console.redhat.com is required, see
[How to configure your platform request tokens](/docs/dev/how-to-configure-platform-request.md).

### RHEL Lightspeed

We can connect to RHEL lightspeed to forward some questions - it is currently available for internal uses in the
stage environment. Make sure to set the environment variable `RHEL_LIGHTSPEED_ENABLED=true` and configure the access 
to the stage environment.

## Testing
Tests can be found on [tests](/services/virtual-assistant/tests) and are run by invoking `make tests` on the root of the project. The tests
use `pytest` as a runner.
