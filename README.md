# WCL-dk-analysis

[Chrome Extension](https://chrome.google.com/webstore/detail/wcl-dk-analysis/bdcgiccpmhdchjjglgompcacmknbbhkj)

[Firefox Extension](https://addons.mozilla.org/en-US/firefox/addon/wcl-dk-analysis/)

[Edge Extension](https://microsoftedge.microsoft.com/addons/detail/wcl-dk-analysis/iooghgeinlkefmpflafiheegonbcbkkk)

# Running the WCL DK Analyzer for Cataclysm Classic Chrome Extension Locally

To run the WCL DK Analyzer for Cataclysm Classic Chrome extension locally, it is recommended to use Google Chrome over other browsers like Firefox or Edge. This guide will walk you through the process of setting up the extension for local development.

## Prerequisites

- Python 3.9 installed on your system

## Installation

1. Download the WCL DK Analyzer for Cataclysm Classic Chrome extension from the Chrome Web Store:
  [https://chromewebstore.google.com/detail/wcl-dk-analysis/bdcgiccpmhdchjjglgompcacmknbbhkj](https://chromewebstore.google.com/detail/wcl-dk-analysis/bdcgiccpmhdchjjglgompcacmknbbhkj)

2. Load the extension as an unpacked extension in Chrome:
  - Open the Chrome browser and navigate to `chrome://extensions`.
  - Enable "Developer mode" using the toggle switch in the top right corner.
  - Click on "Load unpacked" and select the directory where you downloaded the extension.

3. Obtain the extension ID:
  - After loading the unpacked extension, you will see the extension listed on the `chrome://extensions` page.
  - Copy the extension ID, which is a unique string of characters.

4. Update the `content.js` file:
  - Navigate to the `extensions/src` directory within the extension's codebase.
  - Open the `content.js` file in a text editor.
  - Replace the existing extension ID with the one you copied in the previous step.
  - Save the changes.

## Running the Extension

1. Start the backend server:
  - Open a terminal and navigate to the `backend` directory of the extension.
  - Run the following command to start the backend server:
    ```
    make server
    ```

2. Start the frontend server:
  - Open another terminal and navigate to the `frontend` directory of the extension.
  - Run the following command to start the frontend server:
    ```
    make server
    ```

3. Open Chrome and navigate to the desired webpage where you want to use the WCL DK Analyzer for Cataclysm Classic extension.

4. The extension should now be active and running locally.

By following these steps, you will have the WCL DK Analyzer for Cataclysm Classic Chrome extension set up and running locally on your machine. This allows you to make modifications to the extension's code and test them in real-time.

Remember to keep both the backend and frontend servers running while using the extension. If you encounter any issues, make sure to double-check the extension ID and ensure that the servers are running correctly.
