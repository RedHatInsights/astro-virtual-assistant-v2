# How to configure your platform request token

To be able to communicate to services within console.redhat.com, you need to have a valid token to talk with https://console.redhat.com

There are currently supported ways for local development:

- Offline token
- Service account

## Offline token

Generate an offline token for https://sso.redhat.com.
All the API calls will be made on behalf of the user of this token. You can generate an offline token at
[https://access.redhat.com/management/api](https://access.redhat.com/management/api) by clicking "Generate token".
Copy this token to the environment variable `DEV_PLATFORM_REQUEST_OFFLINE_TOKEN` (`.env` file is supported).

> If you want to use the stage environment, generate the token at
> [https://access.stage.redhat.com/management/api](https://access.stage.redhat.com/management/api) and also set the
> environment variable `DEV_PLATFORM_REQUEST_REFRESH_URL` to `https://sso.stage.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token`
>
> You will also need to point the `PLATFORM_URL` environment variable to [https://console.stage.redhat.com](https://console.stage.redhat.com), and make sure that your [http proxy](./proxy.md) url is set up properly.

## Service account

Create a service account on https://console.redhat.com/iam/service-accounts and add it to a group that has the required access for the services you are testing.
Once that's done, copy the `Client id` and `Client secret` to the environment variable `SA_PLATFORM_REQUEST_ID` and `SA_PLATFORM_REQUEST_SECRET` (respectively).
(`.env file is supported`)

> If you want to use the stage environment, generate the token at https://console.stage.redhat.com/iam/service-accounts and also set the environment variable
> `SA_PLATFORM_REQUEST_TOKEN_URL` to `https://sso.stage.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token`
> 
> You will also needf to point the `PLATFORM_URL` environment variable to [https://console.stage.redhat.com](https://console.stage.redhat.com), and make sure that your [http proxy](./proxy.md) url is set up properly.