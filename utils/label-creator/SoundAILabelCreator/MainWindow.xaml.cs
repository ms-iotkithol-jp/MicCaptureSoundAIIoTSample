using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.IO;
using Microsoft.Azure.Devices;
using System.Diagnostics;
using Microsoft.Azure.Storage.Blob;
using Microsoft.Azure.Storage;

namespace SoundAILabelCreator
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            this.Loaded += MainWindow_Loaded;
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            var now = DateTime.Now;
            this.tbExportStartTimeStamp.Text = now.ToString("yyyy/MM/dd 00:00:00");
            this.tbExportEndTimeStamp.Text = now.ToString("yyyy/MM/dd 23:59:59");
        }

        List<string> labels = new List<string>();
        CloudBlobClient blobClient;
        private void buttonConfigFile_Click(object sender, RoutedEventArgs e)
        {
            labels.Clear();
            var configFileName = tbConfigFile.Text;
            if (File.Exists(configFileName))
            {
                using (var reader = new StreamReader(File.OpenRead(configFileName)))
                {
                    var yamlDeserializer = new YamlDotNet.Serialization.Deserializer();
                    var yamlObject = yamlDeserializer.Deserialize(reader);
                    var yamlJsonStr = Newtonsoft.Json.JsonConvert.SerializeObject(yamlObject);
                    dynamic configJson = Newtonsoft.Json.JsonConvert.DeserializeObject(yamlJsonStr);
                    if (!(configJson["iot-hub"] is null))
                    {
                        dynamic iotHubDef = configJson["iot-hub"];
                        tbIoTHubCS.Text = iotHubDef["connection-string"];
                        tbEdgeName.Text = iotHubDef["edge-name"];
                        buttonConnectToIoTHub.IsEnabled = true;
                    }
                    if (!(configJson["storage-account"] is null))
                    {
                        dynamic storageAccountDef = configJson["storage-account"];
                        tbStorageCS.Text = storageAccountDef["connection-string"];
                        tbStorageFolder.Text = storageAccountDef["container-name"];
                        CloudStorageAccount storageAccount;
                        try{
                            if (CloudStorageAccount.TryParse(tbStorageCS.Text, out storageAccount))
                            {
                                blobClient = storageAccount.CreateCloudBlobClient();
                                AddLog("Connected to Azure Storage Account.");
                            }
                            buttonBeginInLabel.IsEnabled = true;
                            buttonSaveLabelDefFile.IsEnabled = true;
                        }
                        catch (Exception ex)
                        {
                            AddLog(ex.Message, true);
                        }
                    }
                    if (!(configJson["labels"] is null))
                    {
                        foreach (var l in configJson["labels"])
                            labels.Add(l.Value);
                    }
                }
                lstBoxLabel.ItemsSource = labels;
            }
        }

        RegistryManager registryManager;
        private async void buttonConnectToIoTHub_Click(object sender, RoutedEventArgs e)
        {
            registryManager = RegistryManager.CreateFromConnectionString(tbIoTHubCS.Text);
            try
            {
                await registryManager.OpenAsync();
                tbIoTHubStatus.Text = "Connected";
                buttonDisconnectFromIoTHub.IsEnabled = true;
                buttonConnectToIoTHub.IsEnabled = false;
                AddLog("Connected to IoT Hub.");
            }
            catch (Exception ex)
            {
                AddLog(ex.Message, true);
            }
        }

        private async void buttonDisconnectFromIoTHub_Click(object sender, RoutedEventArgs e)
        {
            try{
                await registryManager.CloseAsync();
                buttonDisconnectFromIoTHub.IsEnabled = false;
                buttonConnectToIoTHub.IsEnabled = true;
                tbIoTHubStatus.Text = "Disconnected";
                registryManager = null;
                AddLog("Disconnected from IoT Hub.");
            }
            catch (Exception ex)
            {
                AddLog(ex.Message,true);
            }
        }

        private async Task MarkLabel(bool isStart)
        {
            var twinsProps = await registryManager.GetTwinAsync(tbEdgeName.Text, soundCaptureModuleName);
            var desiredProps = twinsProps.Properties;
            
            desiredProps.Desired["capture-spec"]["capture-order"] = isStart;
            if (desiredProps.Desired.Contains("classify-on-edge"))
                desiredProps.Desired["classify-on-edge"] = null;
            await registryManager.UpdateTwinAsync(tbEdgeName.Text,soundCaptureModuleName, twinsProps, twinsProps.ETag);
            await Task.Delay(500);
            string currentStatus = "start";
            if (!isStart)
                currentStatus = "end";
            
            currentLabelName = lstBoxLabel.SelectedItem.ToString();
            var blobName = String.Format("{0}-{1}-{2}-{3}.txt", tbEdgeName.Text, DateTime.Now.ToString(timestampNumFormat), currentLabelName, currentStatus );
            var container = blobClient.GetContainerReference(tbStorageFolder.Text);
            var newBlob = container.GetBlockBlobReference(blobName);
            var edgeIdBuf = System.Text.Encoding.UTF8.GetBytes(tbEdgeName.Text);
            await newBlob.UploadFromByteArrayAsync(edgeIdBuf, 0, edgeIdBuf.Length);

            AddLog(string.Format("Marked {0} Lavel={1}",currentStatus, currentLabelName));
        }
        string soundCaptureModuleName = "soundcapturemodule";
        string currentLabelName = "";
        private async void buttonBeginInLabel_Click(object sender, RoutedEventArgs e)
        {
            if (lstBoxLabel.SelectedItem==null)
            {
                MessageBox.Show("Please select label!");
                return;
            }
            buttonEndInLabel.IsEnabled = true;
            if (registryManager!=null)
            {
                try
                {
                    await MarkLabel(true);
                }
                catch (Exception ex)
                {
                    AddLog(ex.Message, true);
                }
            }
            buttonBeginInLabel.IsEnabled = false;
        }
        private async void buttonEndInLabel_Click(object sender, RoutedEventArgs e)
        {
            buttonEndInLabel.IsEnabled = false;
            if (registryManager!=null)
            {
                try
                {
                    await MarkLabel(false);
                }
                catch (Exception ex)
                {
                    AddLog(ex.Message, true);
                }

            }
            buttonBeginInLabel.IsEnabled = true;
        }

        private readonly string timestampNumFormat = "yyyyMMddHHmmss";
        private async void buttonSaveLabelDefFile_Click(object sender, RoutedEventArgs e)
        {
            var selectedDef = cmbBoxLabelDefFileType.SelectedItem as ComboBoxItem;
            var labelDefFileName = selectedDef.Content + tbLabelDefBodyName.Text;
            if (File.Exists(labelDefFileName))
            {
                var result = MessageBox.Show("Do you overwrite existing file?","Alert",MessageBoxButton.YesNo);
                if (result== MessageBoxResult.No)
                {
                    MessageBox.Show("Please change file name!");
                    return;
                }
            }

            List<string> markedFiles = new List<string>();
            try
            {
            var container = blobClient.GetContainerReference(tbStorageFolder.Text);
            BlobContinuationToken token = null;
            do
            {
                var results = await container.ListBlobsSegmentedAsync(null, token);
                token = results.ContinuationToken;
                foreach (var b in results.Results)
                {
                    var blob = b as CloudBlockBlob;
                    markedFiles.Add(blob.Name);
                }
            }
            while (token!=null);
            
            var startRange = long.Parse(DateTime.Parse(tbExportStartTimeStamp.Text).ToString(timestampNumFormat));
            var endRange = long.Parse(DateTime.Parse(tbExportEndTimeStamp.Text).ToString(timestampNumFormat));
            markedFiles.Sort();
            var sb = new StringBuilder();
            var writer = new StringWriter(sb);
            string preStatus ="",preLabel="", preTimeStamp="", preDeviceId="";
            for (var i=0;i<markedFiles.Count;i++)
            {
                string status,label,timestamp, deviceId;
                var fileTimestampNum =  ParseFileName(markedFiles[i],out status, out label, out timestamp, out deviceId);
                if (startRange<=fileTimestampNum && fileTimestampNum<=endRange)
                {
                    if (preStatus=="start" && status=="end" && preLabel==label && preDeviceId==deviceId)
                    {
                        writer.WriteLine("{0},{1},{2}",label, preTimeStamp, timestamp);
                    }
                    preStatus = status;
                    preLabel = label;
                    preTimeStamp = timestamp;
                    preDeviceId = deviceId;
                }
            }
            
            if (File.Exists(labelDefFileName))
            {
                File.Delete(labelDefFileName);
                AddLog("Existed file has been deleted.");
            }
            using (var fs = File.Open(labelDefFileName,FileMode.CreateNew,FileAccess.Write))
            {
                var labelDefs = writer.ToString();
                var buf = System.Text.Encoding.UTF8.GetBytes(labelDefs);
                await fs.WriteAsync(buf,0,buf.Length);
                AddLog("File Stored.");
            }
            }
            catch (Exception ex)
            {
                AddLog(ex.Message, true);
            }
        }

        private long ParseFileName(string fileName, out string status, out string label, out string timestamp, out string deviceId)
        {
            var m0 = fileName.Substring(0,fileName.Length-".txt".Length);
            status = m0.Substring(m0.LastIndexOf("-")+1);
            var m1 = m0.Substring(0,m0.LastIndexOf("-"));
            label = m1.Substring(m1.LastIndexOf("-")+1);
            var m2 = m1.Substring(0,m1.LastIndexOf("-"));
            var t = m2.Substring(m2.Length-"00000000000000".Length);
            deviceId = m2.Substring(0, m2.Length - t.Length);
            timestamp = string.Format("{0}/{1}/{2} {3}:{4}:{5}", t.Substring(0,4),t.Substring(4,2),t.Substring(6,2),t.Substring(8,2),t.Substring(10,2),t.Substring(12,2));
            return long.Parse(t);
        }

        private void AddLog(string text, bool isError=false)
        {
            var sb = new StringBuilder(tbActivityLog.Text);
            var writer = new StringWriter(sb);
            var timestamp = DateTime.Now.ToString("yyyy/MM/dd HH:mm:ss");
            var title = timestamp;
            if (isError)
            {
                title += "[Error]";
            }
            writer.WriteLine(title);
            writer.WriteLine(text);
            writer.WriteLine("");
            tbActivityLog.Text = writer.ToString();
            tbActivityLog.ScrollToEnd();
        }
    }
}
