# Setup Instructions

## Prerequisites

1. Ensure that **Node.js v18** is installed on your system. You can verify the installation by running

   ```
   node -v
   ```

2. Install **conda** if it is not already available.

## Environment Setup

1. Create a new conda environment with Python 3.12

   ```
   conda create -n coding_challenge python=3.12
   ```

2. Activate the environment

   ```
   conda activate coding_challenge
   ```

## Repository Setup

1. Clone the project repository

   ```
   git clone https://github.com/sharanyap21/UAVLogViewer.git
   ```

2. Navigate into the project directory

   ```
   cd UAVLogViewer
   ```

3. Install the necessary packages

    *For the frontend:*

    ```
    npm install
    ```

    *For the backend:*

    ```
    pip install -r requirements.txt
    ```

## Google API Key
1. Go to https://aistudio.google.com and sign in with your Google account
2. Click on the **Get API Key** button on the top right corner
3. Click **Create API Key**
4. Store the generated key in a safe location for future use

## Environment Variables

1. Set the Cesium token as an environment variable. Replace `<YOUR_CESIUM_TOKEN>` with your actual token

   ```
   export VUE_APP_CESIUM_TOKEN=<YOUR_CESIUM_TOKEN>
   ```

2. Set the Google API key as an environment variable. Replace `<YOUR_API_KEY>` with your actual key
   ```
   export GOOGLE_API_KEY=<YOUR_API_KEY>
   ```

*(Note: If you are on Windows Command Prompt, use `set` instead of `export`. If you are using PowerShell, use `$env:<ENV_VARIABLE>="<YOUR_TOKEN_OR_KEY>"`.)*

## Running the Project

* Start the frontend:

  ```
  npm run dev
  ```

* Start the backend:

  ```
  python src/server/app.py
  ```