import boto3
import json
import time
pfxclinet = boto3.client('ec2')
paginator = pfxclinet.get_paginator('get_managed_prefix_list_entries')
ssmclient = boto3.client("secretsmanager")
emailclient = boto3.client("ses")

## Global Varible. Adding this on top of the script as it may requires frequent updates.
## Source Email ID has to be a verified email-id. The verificaiton has to be on the SES service on the same region.
#SourceEmailid= "partner.sample.com"
SourceEmailid= "SFTP-Admin@sample.com"

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



def IPV4_Append_Function(IPv4Prefixlist_PrefixID_list,Final_append_Dictlist):
    max_count = len(IPv4Prefixlist_PrefixID_list)
    print("Validation 6 : Initiating : Commencing IP addition process for all the IP's : ", Final_append_Dictlist ) 
    for Append_entries in Final_append_Dictlist:
        IP = Append_entries.get('Cidr')
        count=1
        for ID in IPv4Prefixlist_PrefixID_list:
            print("------------------------------------------------------------------------")
            print("Special Notification : Just FYI : Preparing to add the IP " + IP + " to the prefix list : ", ID)
            Append_Loop_IPv4Prefixlist_Entries= []
            Append_Loop_IPv4Prefixlist_Entries_finallist = []
            Append_Loop_IPv4Response = pfxclinet.describe_managed_prefix_lists(PrefixListIds = [ID])
            Append_Loop_IPv4Prefixlist=Append_Loop_IPv4Response.get('PrefixLists')
            for x in Append_Loop_IPv4Prefixlist:
                Append_Loop_IPv4Prefixlist_Version = x["Version"]
                Append_Loop_IPv4Prefixlist_State = x["State"]
                Append_Loop_IPv4Prefixlist_MaxEntries = x["MaxEntries"]
            Append_Loop_IPv4Prefixlist_Metadata = paginator.paginate(PrefixListId=ID)
            for i in Append_Loop_IPv4Prefixlist_Metadata:
                Append_Loop_IPv4Prefixlist_Entries = (i["Entries"])
                #print("Append_Loop_IPv4Prefixlist_Entries ",Append_Loop_IPv4Prefixlist_Entries)
                for Entries in Append_Loop_IPv4Prefixlist_Entries:
                    Append_Loop_IPv4Prefixlist_Entries_finallist.append(Entries.get("Cidr"))

            print("Special Notification : Just FYI : The prefix list " + ID +" and its version " ,Append_Loop_IPv4Prefixlist_Version, "has a total entry of ",len(Append_Loop_IPv4Prefixlist_Entries_finallist)," and can accomdate max entries of: ", Append_Loop_IPv4Prefixlist_MaxEntries)

            if (len(Append_Loop_IPv4Prefixlist_Entries_finallist) < Append_Loop_IPv4Prefixlist_MaxEntries):
                print("Special Notification : Just FYI : Adding the IP " + IP + " to the prefix list : ", ID)
                try:
                    IPv4PrefixlistUpdate_Response = pfxclinet.modify_managed_prefix_list( CurrentVersion= Append_Loop_IPv4Prefixlist_Version, PrefixListId=ID, AddEntries= [Append_entries])
                    print("Special Notification : Just FYI : successfully added the IP " + IP + " to the prefix list : ", ID)
                    time.sleep(10)
                except: 
                    print("Validation 6: Failed : Failure while adding the "+ IP + " to the prefix list : ", ID)
                    Function_SuperAdminTeam_sendemail("Notification : Issue while updating the Prefix list associated with AWS Trasnfer Family : ", "Failure while appending the IP : "+ IP +" associated prefix list", IP)
                break
            
            else:
                print("Special Notification : Just FYI : Unable to add the IP " + IP + " to the prefix list : " + ID + " as no space avaliable to add more entries. Trying to add the IP's to the other avaliable prefix list.")
                if count == max_count:
                    print("Validation 6: Failed : Unable to add the "+ IP + " to the prefix list as no further space is avaliable prefix list : ", ID)
                    Function_SuperAdminTeam_sendemail("Notification : Issue with Prefix list associated with AWS Trasnfer Family : ", "The IP : "+ IP +" cannot be added as there is no space in any of the associated prefix list", IP)
                    continue
                count=count+1
                    #NotifySupportAdmin



def IPV4_Remove_Function(IPv4Prefixlist_PrefixID_list,removal_list):
    print("Validation 5 : Initiating : Commencing IP removal process for all the IP's : ", removal_list ) 
    for ID in IPv4Prefixlist_PrefixID_list:
        Pop_Loop_IPv4Prefixlist_Entries= []
        Pop_Loop_IPv4Prefixlist_Entries_finallist = []
        Pop_Loop_pop_list = []
        Final_removal_Dictlist =[]
        Pop_Loop_IPv4Response = pfxclinet.describe_managed_prefix_lists(PrefixListIds = [ID])
        Pop_Loop_IPv4Prefixlist=Pop_Loop_IPv4Response.get('PrefixLists')
        for x in Pop_Loop_IPv4Prefixlist:
            Pop_Loop_IPv4Prefixlist_Version = x["Version"]
            Pop_Loop_IPv4Prefixlist_State = x["State"]
        Pop_Loop_IPv4Prefixlist_Metadata = paginator.paginate(PrefixListId=ID)
        for i in Pop_Loop_IPv4Prefixlist_Metadata:
            Pop_Loop_IPv4Prefixlist_Entries = (i["Entries"])
            #print("Pop_Loop_IPv4Prefixlist_Entries ",Pop_Loop_IPv4Prefixlist_Entries)
            for Entries in Pop_Loop_IPv4Prefixlist_Entries:
                Pop_Loop_IPv4Prefixlist_Entries_finallist.append(Entries.get("Cidr"))
        # The below step is to remove any duplicates on the removal list, as same IP's can be provided in different systems.
        removal_list = list( dict.fromkeys(removal_list))
        Pop_Loop_pop_list = set(Pop_Loop_IPv4Prefixlist_Entries_finallist) - (set(Pop_Loop_IPv4Prefixlist_Entries_finallist) - set(removal_list))
        if len(Pop_Loop_pop_list) != 0:
            #print(Pop_Loop_pop_list)
            #print("The above is the pop pop list")
            key = ['Cidr','Description']
            for removal_entry in Pop_Loop_pop_list:
                pop_dictionary = {key[0]:removal_entry}
                Final_removal_Dictlist.append(pop_dictionary)
                                
            try:
                IPv4PrefixlistUpdate_Response = pfxclinet.modify_managed_prefix_list(
                            CurrentVersion= Pop_Loop_IPv4Prefixlist_Version,
                            PrefixListId=ID,
                            #AddEntries= Final_append_Dictlist,
                            RemoveEntries=Final_removal_Dictlist)
                time.sleep(3)
                print("Special Notification : Just FYI : The prefix list " + ID + " has been altered and the following IP's are removed : ", Pop_Loop_pop_list)
            except: 
                print("Failed")
                print("Validation 5 : Failed : Failure while altering the prefix list " + ID + " while removing the IP's : ",Pop_Loop_pop_list)
                Function_SuperAdminTeam_sendemail("Notification : Issue while updating the Prefix list associated with AWS Trasnfer Family : ", "Failure while removing the IP's : "+ Pop_Loop_pop_list +" from the associated prefix list", Pop_Loop_pop_list)
                
    print("Special Notification : Just FYI : All the IP's in the mentioned list has been removed from the prefix list. IP's : ", removal_list )             



def lambda_handler(event, context):
    #To do section of the code.
    ## Get all the CIDR values from prefix list and store it in a variable.
    IPv4Response = pfxclinet.describe_managed_prefix_lists(
        Filters=[
        {'Name': 'prefix-list-name',
         'Values': ['AUTOMATED_PREFIXLIST_IPV4*']}
         ])

    ### Note : Test the script with 1000 IP entries in the prefix list to make sure it is able to manage all the 1000 entries.
    IPv4Prefixlist_Entries_intermediatelist= []
    IPv4Prefixlist_Entries_finallist = []
    IPv4Prefixlist_PrefixID_list = []

    IPv4Prefixlist=IPv4Response.get('PrefixLists')
    for Metadata in IPv4Prefixlist:
        IPv4Prefixlist_Version = Metadata["Version"]
        IPv4Prefixlist_State = Metadata["State"]
        IPv4Prefixlist_PrefixID = Metadata["PrefixListId"]
        #This is to collect all the prefixID
        IPv4Prefixlist_PrefixID_list.append(IPv4Prefixlist_PrefixID)
        IPv4Prefixlist_Entries = paginator.paginate(PrefixListId=IPv4Prefixlist_PrefixID)
        for i in IPv4Prefixlist_Entries:
            IPv4Prefixlist_Entries_intermediatelist.append(i["Entries"])
            #print(IPv4Prefixlist_Entries_intermediatelist)
    #The beow is applicable because, the above output has list with 2 square brackets
    for Entries in IPv4Prefixlist_Entries_intermediatelist:
        for SubEntries in Entries:
            IPv4Prefixlist_Entries_finallist.append(SubEntries.get("Cidr"))
    # At this step, we have the list of all IP's that are configured on the prefix list for a specific IP type. (TPv4 in this case)
    #print(IPv4Prefixlist_Entries_finallist)
    
    print("Validation 1 : Passed : Step 1 completed and all CIDR's has been extracted from the IPv4 prefix list for comparision.")
    
    SSMResponse = ssmclient.list_secrets(
        Filters=[
        {
            'Key': 'name',
            'Values': ['SFTP']
        }
        ])

    #The list secret option doesnot return all secrets by default. The below NextToken handler is to make sure all the secrerts are extracted for validation purpose.
    Final_append_Dictlist = [] #The format in which the IP's needs to be added should be in a dictonary list seperated by comma.
    Final_append_list = [] #This variable will have the list of IP's that needs to be added.
    removal_list = []    # Same as above
    Final_removal_Dictlist =[]  # Same as above
    Full_secretmanager_iplist = []    
    ### Note : Test the same thing with 100+ entries on the secret manager.
    AllSecretlist = SSMResponse["SecretList"]
    while "NextToken" in SSMResponse:
        print("Special Notification : Just FYI : The Secret Manager has more entries that cannot be extracted in one pull request. Hence AWS provided NextToken value and hence interating using the NextToken value to gather all the data.")
        SSMResponse = ssmclient.list_secrets(NextToken=response["NextToken"])
        AllSecretlist.extend(SSMResponse["SecretList"])

    for SSMmetadata in AllSecretlist:
        #AWS metadata and the get request for this will not error or throw any exceptions.
        SecretName = SSMmetadata.get("Name")
        SecretARN = SSMmetadata.get("ARN")
        Secretmetadata = ssmclient.get_secret_value(SecretId=SecretARN)
        SecretKeystring = Secretmetadata["SecretString"]
        SecretKeystring = json.loads(SecretKeystring)
        try:
            SecretIPList = SecretKeystring["IP"].split(',')
        except:
            print("Special Notification : Just FYI : No IPv4 address are avaliable for the user " + SecretName + ". Kindly check with admin team regarding the same.")
            continue
        ## IP's that needs to be added to the Prefix list because it exists in the Secret Manager and does not exists in the Prefixlist/security Group.    
        for IP in SecretIPList:
            Full_secretmanager_iplist.append(IP)
            if IP in IPv4Prefixlist_Entries_finallist:
                ### Disabiling the below comments provides detailed logs.
                print("Special Notification : Just FYI : The IP :" + IP +" avaliable on the secretmanager for the user "+ SecretName +" is avaliable in overall prefix list.")
            else:
                print("Special Notification : Just FYI : The IP :" + IP +" avaliable on the secretmanager for the user "+ SecretName +" is NOT avaliable in the prefix list and hence eligible for addition.")
                Final_append_list.append(IP)
                key = ['Cidr','Description']
                append_dictionary = {key[0]:IP, key[1]:SecretName}
                Final_append_Dictlist.append(append_dictionary)
                ## We are passing the entire dictioanry list instead of just IP's to add the CIDR's to the function because, the Dictionary has IP's and associated comments which cannot be derived just from the above function.

    print("Validation 2 : Passed : Step 2 completed and all IPv4 CIDR's has been extracted from the secretmanager for comparision.")

    ## IP's that needs to be removed from the prefix list as the IP's that existed on the SecretManager has been removed due to change in source system IP's.
    removal_list = set(IPv4Prefixlist_Entries_finallist) - set(Full_secretmanager_iplist)
    
    
    print("Validation 3 : Passed : The list of IPv4 CIDR's that will be added to the prefix list as part of the run : ",  Final_append_list )
    
    
    print("Validation 4 : Passed : The list of IPv4 CIDR's that will be removed from the prefix list as part of the run : ",  removal_list )
    
    
    ################# At this point all information required to add or remove the IP's from the prefix list has been collected. The section of the script will add the entries to the Prefix list or send notficications to the support and admin team incase of a failure in addition process.
    
    ### IP Removal part ###
    if len(removal_list) != 0 :
        IPV4_Remove_Function(IPv4Prefixlist_PrefixID_list,removal_list)
    else:
        print("Validation 5 : Passed : No IPv4 CIDR's in the removal list. Hence the prefix list is not altered as part of the removal process." )
        
    ### IP addition part ###
    if len(Final_append_list) != 0:
        IPV4_Append_Function(IPv4Prefixlist_PrefixID_list,Final_append_Dictlist)
    else : 
        print("Validation 6 : Passed : No IPv4 CIDR's in the append list. Hence the prefix list is not altered to add any IP's." )
    
    #### Completion of script ######
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
