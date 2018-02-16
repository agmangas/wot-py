const WebSocket = require('ws');
const axios = require('axios');
const async = require('async');

const CATALOGUE_URL = 'http://localhost:9292';
const NAME_THING = 'TemperatureThing';
const NAME_PROP_TEMP = 'temperature';
const NAME_PROP_TEMP_THRESHOLD = 'high-temperature-threshold';
const NAME_EVENT_TEMP_HIGH = 'high-temperature';

/**
 * Sends a request to observe the 'High Temperature' event.
 */
function requestObserveTempHigh(ws) {
  const id = Math.floor(Math.random() * 100000);

  const req = {
    id: id,
    jsonrpc: '2.0',
    method: 'on_event',
    params: {
      name: NAME_EVENT_TEMP_HIGH
    }
  };

  const reqStr = JSON.stringify(req);
  console.log('Sending request (on_event):', reqStr);
  ws.send(reqStr);

  return id;
}

/**
 * Sends a request to set the temperature threshold.
 */
function requestSetThreshold(ws, val) {
  const id = Math.floor(Math.random() * 100000);

  const req = {
    id: id,
    jsonrpc: '2.0',
    method: 'write_property',
    params: {
      name: NAME_PROP_TEMP_THRESHOLD,
      value: val
    }
  };

  const reqStr = JSON.stringify(req);
  console.log('Sending request (set threshold):', reqStr);
  ws.send(reqStr);

  return id;
}

/**
 * Sends a request to retrieve the current temperature.
 */
function requestGetTemperature(ws) {
  const id = Math.floor(Math.random() * 100000);

  const req = {
    id: id,
    jsonrpc: '2.0',
    method: 'read_property',
    params: {
      name: NAME_PROP_TEMP
    }
  };

  const returnPromise = new Promise(function (resolve) {
    const messageHandler = function (data) {
      const parsedData = JSON.parse(data);
      if (parsedData.id === id) {
        resolve();
        ws.removeListener('message', messageHandler);
      }
    };

    ws.on('message', messageHandler);
  });

  const reqStr = JSON.stringify(req);
  console.log('Sending request (get temperature):', reqStr);
  ws.send(reqStr);

  return returnPromise;
}

console.log('GET', CATALOGUE_URL);

const tdPromise = axios.get(CATALOGUE_URL)
    .then(function (response) {
      return response.data[NAME_THING];
    })
    .catch(function (error) {
      console.error('Error connecting to:', CATALOGUE_URL);
    });

tdPromise.then(function (td) {
  const propTemp = td.interaction.find(function (interaction) {
    return interaction.name === NAME_PROP_TEMP;
  });

  const wsLink = propTemp.form.find(function (form) {
    return form.href && form.href.startsWith('ws://');
  });

  console.log('Connecting to:', wsLink.href);

  const ws = new WebSocket(wsLink.href);

  ws.on('open', function () {
    console.log('WS connection opened to:', wsLink.href);

    requestObserveTempHigh(ws);

    const threshold = Math.random() * (28.0 - 20.0) + 20.0;

    requestSetThreshold(ws, threshold);

    async.forever(
        function (next) {
          requestGetTemperature(ws).then(next);
        },
        function (err) {
          console.error('Error in forever:', err)
        }
    );
  });

  ws.on('message', function (data) {
    console.log('Message from server:', data);
  });

  ws.on('close', function (err) {
    console.log('Disconnected:', err);
  });
});
