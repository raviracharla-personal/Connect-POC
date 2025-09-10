using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using XFormation;

namespace ThrowMeAwayLicense
{
    class Program
    {
        static void Main(string[] args)
        {
            //LmxLicenseProvider lp = new LmxLicenseProvider();
            //License lic = lp.GetLicense(new LicenseContext(), ,, true);
            LMX lmx = new LMX();
            LMX_STATUS status;

            
            status = lmx.Init();
            Console.WriteLine("Init Result: " + status);

            if (status != LMX_STATUS.LMX_SUCCESS)
            {
                throw new Exception("Init Result was not success. Result Was " + status);
            }

            status = lmx.SetOption(LMX_SETTINGS.LMX_OPT_LICENSE_PATH, "6200@192.168.1.237");
            if (status != LMX_STATUS.LMX_SUCCESS)
            {
                throw new Exception("Failed setting license server. Result Was " + status);
            }

            /*status = lmx.Checkout("Nexus", 1, 0, 1);
            Console.WriteLine("Checkout Result: " + status);

            if (status != LMX_STATUS.LMX_SUCCESS)
            {
                throw new Exception("Failed checking out Nexus License. Result Was " + status);
            }*/

            status = lmx.Checkout("1-1_Matching_API",6,9,101);
            Console.WriteLine("Checkout Result: " + status);

            if (status != LMX_STATUS.LMX_SUCCESS)
            {
                throw new Exception("Failed grabbing NFW license. Result Was " + status);
            }

            status = lmx.Checkin("1-1_Matching_API", 2);
            Console.WriteLine("Checkin Result: " + status);

            if (status != LMX_STATUS.LMX_SUCCESS)
            {
                throw new Exception("Failed checking in NFW license. Result Was " + status);
            }

            Console.WriteLine("Press any key to close");
            Console.ReadKey();
        }
    }
}
