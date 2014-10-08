
KATCP interface for collectd
============================

**collectd** is a daemon which collects system performance statistics periodically 
katcp_collectd.py is used to expose performance statistics collect by collectd as KATCP sensors.

Configuration
-------------

It is necessary to configure katcp_collectd.py

Port and host should be set. When Host is 127.0.0.1 the katcp server will only accept connections from localhost and when
Host is 0.0.0.0 the katcp server will accept connections from every one.

ModulePath is the directory where katcp_collectd.py was checked out to.

Example collectd config.

::

    <Plugin python>
        ModulePath "/usr/local/katcp_collectd"
        LogTraces true
        Import "katcp_collectd"
        <Module katcp_collectd>
            Port 9090
            Host 0.0.0.0
        </Module>
    </Plugin>


