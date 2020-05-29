import os
import sys
import time
import datetime
import io
import asyncio
from updaterbase import FileUpdaterBase

# from azure.storage.blob import BlockBlobService, PublicAccess
from azure.storage.blob.aio import BlobServiceClient

class BlobFileUpdater(FileUpdaterBase):
    def __init__(self,
            blobonedge_module_name,
            blob_account_name,
            blob_account_key,
            sound_container_name,
            edge_id):

        localblob_connectionstring = 'DefaultEndpointsProtocol=http;BlobEndpoint=http://'+blobonedge_module_name+':11002/'+blob_account_name+';AccountName='+blob_account_name+';AccountKey='+blob_account_key+';'
        print("Try to connect to blob on edge by "+localblob_connectionstring)
        self.blobServiceClient = BlobServiceClient.from_connection_string(localblob_connectionstring)
        print("Connected to blob on edge")

        self.containerClient = self.blobServiceClient.get_container_client(sound_container_name)
        self.soundContainerName = sound_container_name

        self.edgeId = edge_id

    async def initialize(self):
        try:
            await self.containerClient.create_container()
            print('Created - {} - container'.format(self.soundContainerName))
        except Exception as e:
            print('Failed to create container - {0}'.format(e))

    async def uploadFile(self, fileName):
        blobName = '{0}-{1}'.format(self.edgeId, os.path.basename(fileName))
        blobClient = self.containerClient.get_blob_client(blobName)
        try:
            with open(fileName,'rb') as data:
                await blobClient.upload_blob(data)
            print('Updated {0} as {1} to Blob on Edge'.format(fileName, blobName))
        except Exception as e:
            print('Upload failed - {}'.format(e))

