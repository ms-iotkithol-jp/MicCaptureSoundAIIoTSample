using IoTHubTrigger = Microsoft.Azure.WebJobs.EventHubTriggerAttribute;

using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Microsoft.Azure.EventHubs;
using System.Text;
using System.IO;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;


namespace EGeorge.SoundAI.Service
{
    public static class IotHubTriggerSoundDataComposer
    {
        private static BlobContainerClient  blobContainerCleint = null;
        private static BlobContainerClient blobContainerOutClient = null;
        private static string blobContainerName = "soundfragment";
        private static string blobContainerOutName = "sounddata";

        [FunctionName("IotHubTriggerSoundDataComposer")]
        public static void Run([IoTHubTrigger("messages/events", Connection = "IoTHubConnectionString")]EventData message, ILogger log)
        {
            string dataType = "";
            string dataTimestamp = "";
            string dataFormat = "";
            string dataLengthStr = "";
            string dataPacketNoStr = "";
            string dataIndexStr = "";

            foreach (var prop in message.Properties)
            {
                switch (prop.Key.ToString().ToLower())
                {
                    case "datatype":
                        dataType = prop.Value.ToString();
                        break;
                    case "datatimestamp":
                        dataTimestamp = prop.Value.ToString();
                        break;
                    case "dataformat":
                        dataFormat = prop.Value.ToString();
                        break;
                    case "datalength":
                        dataLengthStr = prop.Value.ToString();
                        break;
                    case "datapacketno":
                        dataPacketNoStr = prop.Value.ToString();
                        break;
                    case "datapacketindex":
                        dataIndexStr = prop.Value.ToString();
                        break;
                    default:
                        break;
                }
            }
            if (string.IsNullOrEmpty(dataType)||string.IsNullOrEmpty(dataTimestamp)||string.IsNullOrEmpty(dataFormat)||string.IsNullOrEmpty(dataLengthStr)||string.IsNullOrEmpty(dataPacketNoStr)||string.IsNullOrEmpty(dataIndexStr))
            {
                log.LogInformation("Data is not target.");
                return;
            }
            if (dataType!="sound")
            {
                log.LogInformation("DataType is not 'sound'");
                return;
            }
            var dataLength = int.Parse(dataLengthStr);
            var dataPacketNo = int.Parse(dataPacketNoStr);
            var dataIndex = int.Parse(dataIndexStr);
            var deviceId = message.SystemProperties["iothub-connection-device-id"].ToString();
            var data = message.Body.ToArray();
            string blobNameCommon = deviceId + "-sound-" + dataTimestamp + "000000";

            if (blobContainerCleint==null)
            {
                string connectionString = Microsoft.Azure.CloudConfigurationManager.GetSetting("StorageConnectionString");
                blobContainerCleint = new BlobContainerClient(connectionString, blobContainerName);
                blobContainerCleint.CreateIfNotExists();
                blobContainerOutClient = new BlobContainerClient(connectionString, blobContainerOutName);
                blobContainerOutClient.CreateIfNotExists();
            }

            if (dataIndex+1==dataPacketNo)
            {
                // create marged file with current file and uploaded file. after completed , remove uploaded fragment files.
                MergeSoundData(dataPacketNo,dataFormat,blobNameCommon);
            }
            else
            {
                string blobName = blobNameCommon + "." + dataIndex;
                using (var stream = new MemoryStream(data))
                {
                    blobContainerCleint.UploadBlob(blobName, stream);
                }
            }
        }

        static void MergeSoundData(int dataPacketNo, string dataFormat, string blobNameCommon)
        {
            var blobs = blobContainerCleint.GetBlobs();
            List<BlobItem> targetBlobs = new List<BlobItem>();
            byte[] targetContent = null;
            foreach (var blob in blobs)
            {
                if (blob.Name.StartsWith(blobNameCommon))
                {
                    var blobClient = blobContainerCleint.GetBlobClient(blob.Name);
                    var contentLength = blob.Properties.ContentLength;
                    var readBuf = new byte[contentLength.Value];
                    using (var stream = new MemoryStream(readBuf))
                    {
                        blobClient.DownloadTo(stream);
                    }
                    if (targetContent==null)
                    {
                        targetContent = new byte[readBuf.Length];
                        readBuf.CopyTo(targetContent,0);
                    }
                    else
                    {
                        var tmpBuf = new byte[targetContent.Length + readBuf.Length];
                        targetContent.CopyTo(tmpBuf, 0);
                        readBuf.CopyTo(tmpBuf, targetContent.Length);
                        targetContent = tmpBuf;
                    }
                    targetBlobs.Add(blob);
                    if (targetBlobs.Count >= dataPacketNo)
                        break;
                }
            }
            if (targetBlobs.Count==dataPacketNo)
            {
                string mergedBlobName = blobNameCommon + "." + dataFormat;
                if (dataFormat == "csv")
                {
                    var sb = new StringBuilder();
                    using (var writer = new StringWriter(sb))
                    {
                        for (var index = 0; index < targetContent.Length; index += 2)
                        {
                            byte l = targetContent[index];
                            byte h = targetContent[index + 1];
                            int val = ((int)h) << 8 | (int)l;
                            writer.WriteLine(val);
                        }
                    }
                    var mergedCSVContent = System.Text.Encoding.UTF8.GetBytes(sb.ToString());
                    using( var contentReader = new MemoryStream(mergedCSVContent))
                    {
                        blobContainerOutClient.UploadBlob(mergedBlobName, contentReader);
                    }
                }
                else
                {
                    using (var dataStream = new MemoryStream(targetContent))
                    {
                        blobContainerOutClient.UploadBlob(mergedBlobName, dataStream);
                    }
                }
            }
            foreach(var targetedBlob in targetBlobs)
            {
                blobContainerCleint.DeleteBlob(targetedBlob.Name);
            }
        }
    }
}