# HTTP Proxy for accessing stage environment

In order to access stage environment, we require to use the squid proxy.
We need to inform our services about this proxy when running locally. 
Simply add the hostname to the env `HTTPS_PROXY` environment variable to configure it.
