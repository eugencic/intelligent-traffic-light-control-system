# Intelligent Traffic Light Control System

More details can be found in the report.

## Run the application

Before running the application, install [Docker](https://www.docker.com/) on the device.  

Type this command in the root folder to run the main application.

```bash
$ docker compose up --build
```

### Traffic Monitoring Service

Before running the service, install the packages from `requirements.txt`. 

Make sure the main application is already running.

Type this command in the root folder:

```bash
$ python main.py
```

### Traffic Light Simulator

Before running the simulator, install [npm](https://www.npmjs.com/) on the device, and set up `node_modules`. 

Make sure the main application is already running.

Type this command in the root folder:

```bash
$ npm start
```

### Traffic Insights App

Before running the application, install [npm](https://www.npmjs.com/) on the device, and set up [Expo](https://docs.expo.dev/tutorial/create-your-first-app/).

Find `api/intersectionApi.js` in the root folder and add your local IPv4 Address to `API_TRAFFIC_DATA_URL`
and `API_TRAFFIC_INFO_URL` constants.

Make sure the main application is already running.

Type this command in the root folder:

```bash
$ npm start
```

Install [Expo Go](https://expo.dev/go) and run the application on mobile.
