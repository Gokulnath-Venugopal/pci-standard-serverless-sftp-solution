import json
import boto3
import ast
import datetime
import base64,struct,sys,binascii
import re

# Lambda can invoke boto3 clients or resources. All the below actions are clinet invoked actions.
ssmclient = boto3.client("secretsmanager")
emailclient = boto3.client("ses")

#####################################
#####################################
######### Exclusion list ############
#####################################
#####################################
# Any users added to the below list will be excluded and will not send any notifications to banks unless until removed.
Notification_Exclusion_list= ["Sample"]

## Global Varible. Adding this on top of the script as it may requires frequent updates.
## Source Email ID has to be a verified email-id. The verificaiton has to be on the SES service on the same region.
#SourceEmailid= "partner.sample.com"
SourceEmailid= "SFTP-Admin@sample.com"

##The same script will be used for Bank Notification as well as BAU validation when entries are populated on the secret manager. The below parameter enables the developer to comment the bank notification part of the script.
### Update the parameter to True for the BankNotificaiton part of the script.
### Update the parameter to Flase for monitoring and notificaiton to support and admin teams.
Enable_Bank_Notification = True
#Enable_Bank_Notification = False


def Function_SuperAdminTeam_sendemail(Email_Subject, Email_Body, Username):
    # Source email should be a verified domain on the SES.
    # The secret string is mandatory for all users with the secret manager and hence there is no try and except for extracting secretstring. However validations to be done for the values on the secret string.
    # The SuperAdmin is expected to have all the configurations, configured properly like Email & Name.
    SuperAdmin_SecretKeystring = ssmclient.get_secret_value(SecretId='SFTP/SuperAdmin')["SecretString"]
    SuperAdmin_SecretKeystring = json.loads(SuperAdmin_SecretKeystring)
    try:
        SuperAdmin_Emaillist = SuperAdmin_SecretKeystring["Email"].split(",")
        sendemailresponse = emailclient.send_email(
        Source= SourceEmailid ,
        Destination={
            "ToAddresses": SuperAdmin_Emaillist 
            #, "CcAddresses": LinuxSupportTeam
                    },
        Message={
            "Subject": {
                "Charset": "UTF-8",
                "Data": Email_Subject + Username,
            },
            "Body": {
                "Text": {
                    "Charset": "UTF-8",
                    "Data": "Hello Super Admin's," + "\nThis is an automated email from FS SFTP AWS Server to notify the following issue for the user :- "+ Username +" . "+ Email_Body + "\n\nRegards" + "\nProdOps Linux Support Team" + "\nprodops.linux@fs.com"
                }
            }
        }
        )  
    except:
        print("Major Error : Failed : The superadmin does not have email configured. This needs to be addressed on priority")

  
def Function_SupportTeam_sendemail(Email_Subject, Email_Body, Username):
    # Source email should be a verified domain on the SES.
    SuperAdmin_SecretKeystring = ssmclient.get_secret_value(SecretId='SFTP/SuperAdmin')["SecretString"]
    SuperAdmin_SecretKeystring = json.loads(SuperAdmin_SecretKeystring)
    SuperAdmin_Emaillist = SuperAdmin_SecretKeystring["Email"].split(",")
    User_SecretKeystring = ssmclient.get_secret_value(SecretId=Username)["SecretString"]
    User_SecretKeystring = json.loads(User_SecretKeystring)

    
    try:
        GroupAdmin = User_SecretKeystring["GroupAdmin"]
        try:
            GroupAdmin_SecretKeystring = ssmclient.get_secret_value(SecretId=GroupAdmin)["SecretString"]
            GroupAdmin_SecretKeystring = json.loads(GroupAdmin_SecretKeystring)
            GroupAdmin_Emaillist = GroupAdmin_SecretKeystring["Email"].split(",")
        except:
            GroupAdmin_Emaillist = []
    except:
        GroupAdmin = []

    if len(GroupAdmin) == 0:
        GroupAdmin_Emaillist = SuperAdmin_Emaillist
        print("EMail Notification : The GroupAdmin of the user :" + Username + " does exist. However seperate notificaitons will be sent to SuperAdmin as part of the validation. For now notfying super admin : "+ Username)
        Function_SuperAdminTeam_sendemail("Notification : Issue with user's GroupAdmin name : ", "The user : "+ Username +" does not have GroupAdmin configured.", Username)
    elif len(GroupAdmin) != 0 and len(GroupAdmin_Emaillist) == 0:
        GroupAdmin_Emaillist = SuperAdmin_Emaillist
        print("EMail Notification : The GroupAdmin of the user :" + Username + " does not have email configured. However seperate notificaitons will be sent to SuperAdmin as part of the validation. For now notfying super admin : "+ Username)
        Function_SuperAdminTeam_sendemail("Notification : Issue with user's GroupAdmin Email conact : ", "The user : "+ Username +" does not have GroupAdmin configured.", Username)
    else:
        pass

        
    sendemailresponse = emailclient.send_email(
    Source= SourceEmailid ,
    Destination={
        "ToAddresses": GroupAdmin_Emaillist 
        #, "CcAddresses": SuperAdmin_Emaillist
                },
    Message={
        "Subject": {
            "Charset": "UTF-8",
            "Data": Email_Subject + Username,
        },
        "Body": {
            "Text": {
                "Charset": "UTF-8",
                "Data": "Hello All," + "\nThis is an automated email from FS SFTP AWS Server to notify the following issue for the user :- "+ Username +" . "+ Email_Body + "\n\nRegards" + "\nProdOps Linux Support Team" + "\nprodops.linux@fs.com"
            }
        }
    }
    )
    

def Function_BANK_sendemail(Email_Subject, Email_Body, Username):
    # Trigger this function only if its absolutely necessary as it send emails to the banking systems.
    SuperAdmin_SecretKeystring = ssmclient.get_secret_value(SecretId='SFTP/SuperAdmin')["SecretString"]
    SuperAdmin_SecretKeystring = json.loads(SuperAdmin_SecretKeystring)
    SuperAdmin_Emaillist = SuperAdmin_SecretKeystring["Email"].split(",")
    User_SecretKeystring = ssmclient.get_secret_value(SecretId=Username)["SecretString"]
    User_SecretKeystring = json.loads(User_SecretKeystring)
    GroupAdmin = User_SecretKeystring["GroupAdmin"]
    GroupAdmin_SecretKeystring = ssmclient.get_secret_value(SecretId=GroupAdmin)["SecretString"]
    GroupAdmin_SecretKeystring = json.loads(GroupAdmin_SecretKeystring)

    ## If the user dosent have any email id, then send the threshold notification to SuperAdmins.
    if len(User_SecretKeystring["Email"]) == 0:
        User_Emaillist = SuperAdmin_Emaillist
        #print(User_Emaillist)
        print("EMail Notification : The source system for the user" + Username + " does not have Email email configured. However seperate notificaitons will be sent to SuperAdmin as part of email check. For now notfying super admin regarding expiry : "+ Username)
        Function_SuperAdminTeam_sendemail("Notification : Issue with contact email for the user : ", "The user : "+ Username +" does not have contact email configured.", Username)
    else:
        User_Emaillist = User_SecretKeystring["Email"].split(",")
        print(User_Emaillist)
    ## If the Groupadmin dosent have any email id, then send the threshold notification to SuperAdmins
    
    try:
        GroupAdminEmailList = GroupAdmin_SecretKeystring["Email"]
    except:
        GroupAdminEmailList = []
    
    if GroupAdminEmailList == 0:
        GroupAdmin_Emaillist = SuperAdmin_Emaillist
        #print(GroupAdmin_Emaillist)
        print("EMail Notification : The GroupAdmin for the user" + Username + " does not have Email email configured. However seperate notificaitons will be sent to SuperAdmin as part of GroupAdmin email check. For now notfying super admin regarding expiry : "+ Username)
        Function_SuperAdminTeam_sendemail("Notification : Issue with contact email for the user's GroupAdmin : ", "The user : "+ Username +" does not have contact email configured.", Username)
    else:
        GroupAdmin_Emaillist = GroupAdmin_SecretKeystring["Email"].split(",")
        print(GroupAdmin_Emaillist)


    sendemailresponse = emailclient.send_email(
    Source= SourceEmailid ,
    Destination={
        "ToAddresses": User_Emaillist ,
        "CcAddresses": GroupAdmin_Emaillist
                },
    Message={
        "Subject": {
            "Charset": "UTF-8",
            "Data": "SSH Key Roration Notification from FS bcgw.fs.com",
        },
        "Body": {
            "Text": {
                "Charset": "UTF-8",
                "Data": "Hello," + "\n\nThe SSH key used to authenticate your banking institution to FS SFTP AWS server at SecureTrasnfer.partner.fs.com needs rotation. To maintain security and compliance, we request that you: "+ "\n\n    1. Generate a new SSH key for authentication," + "\n    2. Provide the public key to prodops.linux@fs.com" + "\n    3. Provide an indicative date that future connections will be using the new key." + "\n\nNote that this email is auto-generated. If you’re unable to action the above, please pass this email to your IT team to Email us at prodops.linux@fs.com." + "\n\nRegards" + "\nProdOps Linux Support Team" + "\nprodops.linux@fs.com"
            }
        }
    }
    )


def Function_MandatoryValueValidation(SecretKeystringDict,Username):
    # This function is to check the all the mandatory values for any given user
    #print(SecretKeystringDict)
    #SecretKeystringDict.keys().strip()
    if "PublicKey" in SecretKeystringDict and "Name" in SecretKeystringDict and "Email" in SecretKeystringDict and "HomeDirectoryType" in SecretKeystringDict and "HomeDirectoryDetails" in SecretKeystringDict and "GroupAdmin" in SecretKeystringDict and "Role" in SecretKeystringDict and ("IP" in SecretKeystringDict or "IPv6" in SecretKeystringDict):
        print("Validation 1 : Passed : The Username : "+ Username + " has all mandatory key value pairs in the secrets.")
        Error_code = 0
        return Error_code
    else:
        print("Validation 1 : Failed : The Username : "+ Username + " does not have all mandatory key value pairs in the secrets.")
        print("               Skipping all further checks and proceeding with next user")
        Function_SupportTeam_sendemail("Notification : Issue with Mandatory secret attributes for the user : ", "The user does not have all mandatory key values(Name, Email, GroupAdmin, PublicKey, IP or IPv, Role, HomeDirectiryDetails, HomeDirectoryType). Admin team to check and update it accordingly", Username)
        Error_code = 1
        return Error_code    
        

def Function_GroupAdminValueValidation(GroupAdminName,Username):
    # This function is to check the unexpected values in the groupadmin field and sends email to super admin.
    if GroupAdminName in AdminSecretNameList:
        print("Validation 2 : Passed : The Username : "+ Username + " has all correct GroupAdmin value.")
        Error_code = 0
        return Error_code
    else:
        print("Validation 2 : Failed : The GroupAdmin name configured for the Username : "+ Username + " is incorrect.")
        print("               Skipping all further checks and proceeding with next user")
        # Error while sending emails to the below. Check if the email has to be sent to superadmin distro.
        Function_SuperAdminTeam_sendemail("Notification : Issue with GroupAdmin for the user : ", "The GroupAdmin value configured for the user in the secret string value is incorrect. Admin team to check and update it accordingly", Username)
        Error_code = 1
        return Error_code        
        

def Function_ContactEmailDelimiterValidation(ContactEmailString,Username):
    # This function is to check the unexpected values in the contact emails
    if ",," in ContactEmailString or ", ," in ContactEmailString or ";" in ContactEmailString or "|" in ContactEmailString :
        print("Validation 3 : Failed : The contact email delimitter configured for the Username : "+ Username + " is invalid.")
        print("               Skipping all further checks and proceeding with next user")           
        Function_SupportTeam_sendemail("Notification : Issue with Contactemail for the user : ", "The input banks contact email is not comma seperated and is in incorrect format. Admin team to check and update it accordingly", Username)
        Error_code = 1
        return Error_code
    else:
        print("Validation 3 : Passed : The contact email delimitter configured for the Username : "+ Username + " is valid.")
        Error_code = 0
        return Error_code


def Function_ContactEmailValueValidation(ContactEmailString,Username):
    # This function is to check if the values of the emails are in valid format
    if len(ContactEmailString) == 0:
        print("Validation 4 : Ignored : The Username : "+ Username + " does not have any contact email configured. Emails will be sent to GroupAdmin or SuperAdmin based on configs.")
        Function_SupportTeam_sendemail("Notification : Warining with Contactemail for the user : ", "The input user contact email is empty . Admin team to check and update it accordingly", Username)
        Error_code = 0
        return Error_code
    else:
        ContactEmaillist=ContactEmailString.split(",")
        for Email in ContactEmaillist:
            if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", Email):
                print("Validation 4 : Passed : The contact email id : "+ Email +" for the Username : "+ Username + " is in the right format.")
                Error_code = 0
                return Error_code
            else:
                print("Validation 4 : Failed : The contact email id :"+ Email +" or the Username : "+ Username + " is incorrect or not in standard email format.")
                print("                 Skipping all further checks and proceeding with next user")    
                Function_SupportTeam_sendemail("Notification : Issue with Contactemail for the user : ", "The input user contact email "+ Email +" is not a valid email . Admin team to check and update it accordingly", Username)
                Error_code = 1
                return Error_code
                continue
            

def Function_HomeDirectoryValidation(DirectoryType,DirectoryDetails,Username):
    #This function is to check if a PublickKey Value stored in the secret manager has 3 mandatory sections.
    if len(DirectoryType) == 0 or len(DirectoryDetails) == 0:
        print("Validation 5 : Failed : The DirectoryDetails or DirectoryType for the Username : "+ Username + " does not have values in it.")
        print("               Skipping all further checks and proceeding with next user")    
        #Function_SupportTeam_sendemail("Notification : Issue with HomeDirectory for the user : ","The DirectoryDetails or DirectoryType for the Username does not have values in it", Username): 
        Error_code = 1
        return Error_code
               
    else:
        DirectoryDetails=json.loads(DirectoryDetails)
        Keys = []
        Values = []
        for DirectoryDetailslist in DirectoryDetails:
            for i in DirectoryDetailslist.keys():
                Keys.append(i)
            for i in DirectoryDetailslist.values():
                Values.append(i)
        #print(Keys[0])
        #print(Keys[1])
        #print(Values[0])
        #print(Values[1])
        if Keys[0] == "Entry" and Keys[1] == "Target" and Values[0] == "/" and DirectoryType =="LOGICAL" :
            print("Validation 5 : Passed : The DirectoryDetails or DirectoryType for the Username : "+ Username + " has right values.")
            Error_code = 0
            return Error_code
        else:
            print("Validation 5 : Failed : The DirectoryDetails or DirectoryType for the Username : "+ Username + " does not have values in it.")
            print("               Skipping all further checks and proceeding with next user") 
            Function_SupportTeam_sendemail("Notification : Issue with HomeDirectory for the user : ", "The values provided for the HomeDirectory is incorrect. Kindly update it inorder for the bank systems to place files properly", Username)
            Error_code = 1
            return Error_code
        
    
def Function_RoleValidation(Role,Username):
    #This function is to if the Role has right value. This needs to be validated again as this is not right.
    # All users will have same role. The role will provide full access to all its subdirectories.
    if len(Role) == 0:
        print("Validation 6 : Failed : The Roles for the Username : "+ Username + " does not have IAM role value in it.")
        print("               Skipping all further checks and proceeding with next user") 
        Function_SupportTeam_sendemail("Notification : Issue with Role for the user : ", "No IAM roles values are provided. Kindly update it inorder for the external systems to place files properly", Username)
        Error_code = 1
        return Error_code
    elif ":role/TransferS3AccessRole" in Role:
        print("Validation 6 : Passed : The Roles for the Username : "+ Username + " has necessary IAM rolename.")
        Error_code = 0
        return Error_code
    else:
        print("Validation 6 : Failed : The Roles for the Username : "+ Username + " has incorrect IAM role value in it.")
        print("               Skipping all further checks and proceeding with next user") 
        Function_SupportTeam_sendemail("Notification : Issue with Role for the user : ", "The values provided for the Role is incorrect. Kindly update it inorder for the bank systems to place files properly", Username)
        Error_code = 1
        return Error_code
        

def Function_IPValueValidation(Username):
    User_SecretKeystring = ssmclient.get_secret_value(SecretId=Username)["SecretString"]
    User_SecretKeystring = json.loads(User_SecretKeystring)
    #print(User_SecretKeystring)
    try:
        IPlist = User_SecretKeystring["IP"]
    except:
        IPlist = []
        
    try:
        IPv6list = User_SecretKeystring["IPv6"]
    except:
        IPv6list = []
    
    if len(IPlist) == 0 and len(IPv6list) == 0:
        print("Validation 7 : Ignored : The system with Username : "+ Username + " does not have any IP address configured for inbound connection.")
    else:
        print("Validation 7 : Passed : The system with Username : "+ Username + " has IP address configured for inbound connection.")
        #Function_SupportTeam_sendemail(Email_Subject, Email_Body, Username):

        #Send email notificaiton to GroupAdmin about it
        #Function_SupportTeam_sendemail(Email_Subject, Email_Body, Username):

    #for IP in IPv4list:
    #    if re.match(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(/(3[0-2]|2[0-9]|1[0-9]|[0-9]))?$", IP):
    #        print("All IPv4 IP is the right format for the user : "+ Username)
    #        Error_code = 0
    #        return Error_code
    #    else:
    #        print("The input user's IPv4 IP "+ IP +" is not a valid. Kindly check.")
    #        Function_SupportTeam_sendemail("Notification : Issue with Contactemail for the user : ", "The input user contact email "+ Email +" is not a valid email . Admin team to check and update it accordingly", Username)
    #        Error_code = 1
    #        return Error_code
    #        continue        

    #for IP in IPv6list:
    #    if re.match(r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(\/((1(1[0-9]|2[0-8]))|([0-9][0-9])|([0-9])))?$", IP):
    #        print("All contact email id's is the right format for the user : "+ Username)
    #        Error_code = 0
    #        return Error_code
    #    else:
    #        print("The input user's IPv6 IP "+ IP +" is not a valid. Kindly check.")
    #        Function_SupportTeam_sendemail("Notification : Issue with Contactemail for the user : ", "The input user contact email "+ Email +" is not a valid email . Admin team to check and update it accordingly", Username)
    #        Error_code = 1
    #        return Error_code
    #        continue        


def Function_SSHKeyStructureValidation(PublikeyList,Username):
    #This function is to check if a PublickKey Value stored in the secret manager has 3 mandatory sections.
    # 1. The ssh key format (ssh-rsa) - 
    # 2. The encrypted key (The contents follows ssh-rsa) ## Updated on 26Nov2021. Based on discussion with team, the SSH key format validation is not required because, banks or external systems may not have ssh keys that are base64 encoded always. Hence this check may fail for certain systems causing interruption. Hence this needs to be removed.
    # 3. The Updated(YYYYMMDD)= value as the last part of the comment, indicating when the specific key was last updated. The notificaitons to Banks, asking for new keys will be sent based on this value.
    ## FuctionVariables ##
    ## PublicKeyCount denotes cont of ssh keys stored in the secret manager. the max can be 2.
    ## CountCheck is a localVariable of this function
    PublicKeyCount=len(PublikeyList)
    MonthDifferencelist=[]
    Error_code = 0
    
    # Only 2 PublicKeys can be accomodated in the SecretManger. If there are more than 2 keys in the secret manager for a sepecific user, then the check would fail and will send email to Group Admin team.
    if PublicKeyCount == 0:
        print("Validation 8 : Failed : The PublicKey for the Username : "+ Username + " does not have any values in it.")
        print("                 Skipping all further checks and proceeding with next user")
        Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The PublicKey does not have any values in it.", Username)
        Error_code=1
        return Error_code
        #continue
    elif PublicKeyCount > 2:
        print("Validation 8 : Failed : The PublicKey for the Username : "+ Username + " has more than accepted values of key (i.e:2) values in it.")
        print("                 Skipping all further checks and proceeding with next user")
        Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The count of public keys for the user is more than 2. Admin team to check and update it accordingly", Username)
        Error_code = 1
        return Error_code
    else:
        ## Keys is the localVariable of this function
        ## For loop to check all the list of publickkeys
        for Keys in PublikeyList:
            Array=Keys.split()
            if len(Array) > 4:
                print("Validation 8 : Failed : The PublicKey for the Username : "+ Username + " has more than 4 compoenets in it (ssh-rsa, the key, commentsection-1(user& server). This is incorrect.")
                print("                 Skipping all further checks and proceeding with next user")
                Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The PublicKey has more than 4 components (ssh-rsa, the key, commentsection-1(user& server), commentsection2-udpatedtime. Admin team to check and update it accordingly", Username)
                Error_code=1
                return Error_code
                continue
            else:
                Typeofkey=Array[0]
                Keystring=Array[1]
                Keyusername=Array[2]
                Keyupdatedate=Array[-1]
                Keyupdatedatelist=Keyupdatedate.split("=")
                KeyLastupdateddate=Keyupdatedatelist[1]
                Todaydate=datetime.datetime.now().strftime("%Y%m%d")
                Daysdifference = int(Todaydate) - int(KeyLastupdateddate)
                MonthDifference = Daysdifference % 31
                MonthDifferencelist.append(MonthDifference)
                # All the informations about the ssh keys, lastupdateddate provided in the ssh key, how old is it based on current date is calculated to send notifications to bank.
                
                ## The below if function validates the part "Updated(YYYYMMDD)=20211221". It validates the date and time format & Updated(YYYYMMDD) format.
                if Keyupdatedatelist[0] == "Updated(YYYYMMDD)":
                    print("Validation 8.1 : Passed : The Updated(YYYYMMDD) for the Username : "+ Username + " is in the right format.")
                    try:
                        datetime.datetime.strptime(Keyupdatedatelist[1], "%Y%m%d")
                        print("Validation 8.2 : Passed : The user provided threshold date for the Username : "+ Username + " is in the right format.")
                    except ValueError:
                        print("Validation 8.2 : Failed : The user provided threshold date for the Username : "+ Username + " is incorrect.")
                        print("                 Skipping all further checks and proceeding with next user")
                        Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The updated date format associated with the PublicKey is not in YYYYMMDD format.", Username)
                        Error_code=1
                        return Error_code
                        continue
                else:
                    print("Validation 8.1 : Failed : The Updated(YYYYMMDD) for the Username : "+ Username + " is not the right format")
                    print("                 Skipping all further checks and proceeding with next user")
                    Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The Updated(YYYYMMDD) keyword associated with the PublicKey has typo.", Username)
                    Error_code=1
                    return Error_code
                    continue
                
                ## Validate if the individual values of the public keys are in the expected format and count.
                ## Updated on 26Nov2021. Based on discussion with team, the SSH key format validation is not required because, banks or external systems may not have ssh keys that are base64 encoded always. Hence this check may fail for certain systems causing interruption. Hence this needs to be removed.
                #try :
                #    Decodedkeystring=base64.b64decode(Keystring)
                #    print(type(Decodedkeystring))
                #    print(Decodedkeystring)
                #    a=4
                #    try :
                #	    str_len = struct.unpack(">I", Decodedkeystring[:a])[0]
                #	    #print("checking if this is working")
                #	    #print(str_len)
                #	    #print(Decodedkeystring[a:a+str_len])
                #	    Decodedkeystring_1=Decodedkeystring[a:a+str_len]
                #	    Decodedkeystring_1=str(Decodedkeystring_1,"utf-8")
                #	    print("The ssh-rsa validation is succesful")
                #    except struct.error :
                #	    print("The SSH Public key is not valid key.")
                #	    Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The SSH Public key is not valid key.", Username)
                #	    Error_code=1
                #	    return Error_code
                #	    continue
                #except binascii.Error:
                #    print("Error while decoding the SSH PublicKey")
                #    Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "Error while decoding the SSH PublicKey.", Username)
                #    Error_code=1
                #    return Error_code
                #    continue
                #    #sendemailtosupportteam
                
                #if Decodedkeystring_1 == Typeofkey and int(str_len) == int(7):
                #    print("Valid ssh key sent by the source system")
                #else:
                #    print("last step, is it failing here")
                #    print("not valid ssh key")
                #    Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The SSH Public key is not valid key.", Username)
                #    Error_code=1
                #    return Error_code
                #    continue
    
    #The above loop will be performed to all PublicKeys associated with a user. And all the difference of lastupdatedtime minus the current date timestamp will be added to the below list to validate if the minimum of the value is less than 10 months.
    # The below function will send notificaiton to Banksystems.
    #print(MonthDifferencelist)
    #print(max(MonthDifferencelist))
    MaxMonthDifference=max(MonthDifferencelist)

    if Error_code == 1:
        pass
    elif MaxMonthDifference < 0 :
        print("Validation 8.3 : Failed : The difference in month between the user provded date and current date is in negative for the : "+ Username + " is incorrect.")
        print("                 Skipping all further checks and proceeding with next user")
        Function_SupportTeam_sendemail("Notification : Issue with PublicKey for the user : ", "The Updated(YYYYMMDD) keyword associated with the PublicKey has issues.", Username)
        Error_code=1
        return Error_code
    elif MaxMonthDifference < 10 and Error_code == 0 :
        print("Validation 8.3 : Passed : The Publickey expiry date for the User : "+ Username + " is under threshold.")
        Error_code=0
        return Error_code
    elif MaxMonthDifference > 10 and MaxMonthDifference < 12 and Error_code == 0 :
        print("Validation 8.3 : Passed : The Publickey expiry date for the User : "+ Username + " is about to expire soon.")
        #NotifyNBank
        if Enable_Bank_Notification == True:
            Function_BANK_sendemail("Notification : The SSH key is about to expire. ", "The SSH key is about to expire. Kindly send an updated key", Username)
        Error_code=0
        return Error_code
    elif MaxMonthDifference == 12 and Error_code == 0 :
        print("Validation 8.3 : Passed : The Publickey expiry date for the User : "+ Username + " is expired and external system needs to provide udpated SSH key.")
        #NotifyNBank
        if Enable_Bank_Notification == True:
            Function_BANK_sendemail("Notification : The SSH key has exeededed the threshold", "This is to Notify bank to provide udpated the key", Username)
        Error_code=0
        return Error_code
    else:
        print("Validation 8.3 : Passed : The Publickey expiry date for the User : "+ Username + " is expired and external system needs to provide udpated SSH key.")
        #NotifyNBank
        if Enable_Bank_Notification == True:
            Function_BANK_sendemail("Notification : The SSH key has exeededed the threshold and not PCI compliant", "This is to Notify bank to provide udpated the key", Username)
        Error_code=0
        return Error_code
        

def lambda_handler(event, context):
    # TOOD implement
    # Get list of all users from secret manager
    response = ssmclient.list_secrets(
        Filters=[
        {
            'Key': 'name',
            'Values': ['SFTP']
        },
    ]
    )
    #The list secret option doesnot return all secrets by default. The below NextToken handler is to make sure all the secrerts are extracted for validation purpose.
    AllSecretlist = response["SecretList"]
    while "NextToken" in response:
        #print("Did the solution get into this")
        response = ssmclient.list_secrets(NextToken=response["NextToken"])
        AllSecretlist.extend(response["SecretList"])
    ## Identify all admin users from the secretmanager list.
    #The value is congifured as glocal value as it is being used in the ablove functions without being passed as a parameter.
    global AdminSecretNameList
    AdminSecretNameList = []
    for SSMmetadata in AllSecretlist:
        SecretName = SSMmetadata.get("Name")
        if "admin" in SecretName.lower() or "groupadmin" in SecretName.lower() or "superadmin" in SecretName.lower():
            AdminSecretNameList.append(SSMmetadata.get("Name"))
    ###########################################
    #Do checks for all individual users. Checks will different if its an GroupAdmin or SuperAdmin compared to other normal users.
    
    for SSMmetadata in AllSecretlist:
        #AWS metadata and the get request for this will not error or throw any exceptions.
        SecretName = SSMmetadata.get("Name")
        SecretARN = SSMmetadata.get("ARN")
        #SecretLastChangedDate = SSMmetadata.get("LastChangedDate")
        Secretmetadata = ssmclient.get_secret_value(SecretId=SecretARN)
        SecretKeystring = Secretmetadata["SecretString"]
        SecretKeystring = json.loads(SecretKeystring)
        print("---------------------------------------------------------------------------------")
        print("Validating the user : "+ SSMmetadata.get("Name"))
        print("---------------------------------------------------------------------------------")
        ## The below part of the script will call functions and pass arguments to validate the data in the secretmanager for all users.
        if SecretName.lower() not in (Exclusion_list.lower() for Exclusion_list in Notification_Exclusion_list):
            Mandate_value_val = Function_MandatoryValueValidation(SecretKeystring,SecretName)
            if Mandate_value_val == 0:
                GroupAdmin=SecretKeystring["GroupAdmin"]
                GrpAdm_value_val = Function_GroupAdminValueValidation(GroupAdmin,SecretName)
                if GrpAdm_value_val == 0:
                    Conact_delimt_val = Function_ContactEmailDelimiterValidation(SecretKeystring["Email"],SecretName)
                    if Conact_delimt_val  == 0:
                        Conact_value_val = Function_ContactEmailValueValidation(SecretKeystring["Email"],SecretName)
                        if Conact_value_val == 0:
                            HomeDir_Val = Function_HomeDirectoryValidation(SecretKeystring["HomeDirectoryType"],SecretKeystring["HomeDirectoryDetails"],SecretName)
                            if HomeDir_Val == 0:
                                Role_Val = Function_RoleValidation(SecretKeystring["Role"],SecretName)
                                if Role_Val == 0:
                                    Function_IPValueValidation(SecretName)
                                    AllPublicKeys=SecretKeystring["PublicKey"].split(",")
                                    Function_SSHKeyStructureValidation(AllPublicKeys,SecretName)
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                else:
                    continue
            else:
                continue
    return {
        "statusCode": 200,
        "body": json.dumps("Hello from Lambda!")
    }
