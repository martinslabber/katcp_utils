
import katcp
from katcp.core import Sensor
import collectd


class KatcpServer(katcp.DeviceServer):

    """The KatCP server where sensor values will be registered."""

    def __init__(self, host, port):
        super(KatcpServer, self).__init__(host, port)
        self.sensor_db = {}
        self._send_inteface_change = False

    def setup_sensors(self):
        self.restarted = False

    def collectd_sensor_update(self, sensor_name, value_time, status, value):
        """Update the sensor value, register the sensor if it do not exists."""
        if sensor_name not in self.sensor_db:
            description = ''
            units = ''
            params = None
            sensor_obj = Sensor(type(value), sensor_name,
                                description, units, params)
            self.sensor_db[sensor_name] = sensor_obj
            self.add_sensor(sensor_obj)
            self._send_interface_change = True
        self.sensor_db[sensor_name].set(value_time, status, value)
        if self._send_interface_change:
            # first update the sensor value then send out the inform
            # to tell connected clients that a sensor was added.
            msg = katcp.Message.inform('interface-changed',
                                       'sensor', sensor_name, 'added')
            self._send_interface_change = False
            self.mass_inform(msg)


class KatcpCollectd(object):

    """Interface to collectd."""

    def __init__(self):
        self.config = {'port': 9999, 'host': '127.0.0.1'}

    def collectd_configure(self, config):
        """Callback for passing config from collectd."""
        for setting in config.children:
            self.config[str(setting.key).lower()] = setting.values[0]

    def collectd_init(self):
        """Callback when collectd initialise."""
        self.server = KatcpServer(self.config['host'],
                                  int(self.config['port']))
        self.server.start()

    def _store(self, sensor_name, value_time, value):
        status = Sensor.NOMINAL
        self.server.collectd_sensor_update(sensor_name,
                                           value_time, status, value)

    def collectd_write(self, vl, data=None):
        """Callback when collectd has a new sensor value."""
        name_segments = []

        for item in [vl.plugin, getattr(vl, 'plugin_instance', None),
                     vl.type, getattr(vl, 'type_instance', None)]:
            if item:
                item = str(item).lower().replace('-', '_')
                if item not in name_segments:
                    name_segments.append(item)

        name = '.'.join(name_segments)
        if name == 'load':
            self._store(name + '1', vl.time, vl.values[0])
            self._store(name + '5', vl.time, vl.values[1])
            self._store(name + '15', vl.time, vl.values[2])
        elif vl.plugin in ['interface', 'netlink'] and len(vl.values) > 1:
            for key, value in zip(['tx', 'rx'], vl.values):
                self._store(name + '.' + key, vl.time, value)
        else:
            self._store(name, vl.time, vl.values[0])

    def collectd_shutdown(self):
        """Callback when collectd shutdown."""
        self.server.stop()

kc = KatcpCollectd()

collectd.register_config(kc.collectd_configure, name='katcp_collectd')
collectd.register_write(kc.collectd_write)
collectd.register_init(kc.collectd_init)
collectd.register_shutdown(kc.collectd_shutdown)
#
