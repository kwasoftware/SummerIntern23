import json
import csv
import synonyms
import statistics
from datetime import datetime

with open(r"C:\Users\rxu37\Downloads\li_company_member_json_202305\li_company_member_json_202305\568d5858da8a862f6930b20e77d08477.json\profiles.json", encoding="utf-8") as f:
    data = json.load(f)


jobAbr  = ["IT", "ITIL", "AI", "BI", "Java", "UX", "Python", "PHP"] 
job = ["Software", "Hardware", "Blockchain", "Data Scientist", "Data Engineer", "Agile", "Cybersecurity", "QA Engineer", "QA Tester",
       "Full Stack", "Frontend", "Backend"]

#extracts all the IT jobs in the list of profiles, so if the title contains keywords in the jobAbr/job array, then the profile is added
def getProfiles(data, jobAbr, job) :  
    profileList = []
    for idx, x in enumerate(data) :
        if data[idx]['title'] is not None :
              arr = data[idx]['title'].split()
              if any(match in arr for match in jobAbr) or any(match in data[idx]['title'] for match in job) :
                 profileList.append(x)
    return profileList
    

profileList = getProfiles(data, jobAbr, job)


# finds duration of time at a certain job
def extract_experience(experience_data, months):
    experience = set() #everytime linkedin updates it sometimes adds many duplicates, so I use a set to get each unique experience

    for entry in experience_data:
        if entry['duration'] is None or entry['date_from'] is None: #if there are no durations/start dates I just skip
            continue

        string_date = entry['date_from'] #start date of the job in the format "month year" or "year"
        parts = string_date.split()

        if len(parts) == 2 and parts[0] in months: #this is the "month year" format and only takes months in english
            numMonths = datetime.strptime(parts[0], "%B").month  #months to integer so january is 1 up until december which is 12
            numYears = int(parts[1]) * 100 #multiple years by 100 to place more value on years since time will be sorted later
            duration = entry['duration'].split() #job duration is the format "# years # months" or "# months", not sure if "# years" case exists but I added cases for it nonetheless
            total_months = 0
            if len(duration) == 2 :  # "# years" or "# months" case
                if duration[1] == "years" :
                    total_months = int(duration[0]) * 12
                else :
                    total_months = int(duration[0])
            elif len(duration) == 4 : #"# years # months" case 
                    if duration[0] == "less" :
                        total_months = 6
                    else :
                        total_months = int(duration[0]) * 12 + int(duration[2])              
            if total_months >= 0 and entry['title'] is not None: #list of tuples in the format(yearmonth, months at job, job title) for yearmonth jan 2014 would be 201401, so 2014 *100 + 1 = 201400 + 1
                        experience.add((numMonths + numYears, total_months, entry['title']))         
        elif len(parts) == 1: #similar as above but this time it is just year
            year = int(parts[0]) * 100
            duration = entry['duration'].split()
            total_months = 0
            if len(duration) == 2 :
                if parts[0] in months :   
                    if duration[1] == "years" :
                        total_months = int(duration[0]) * 12
                    elif duration[3] == "months" :
                        total_months = int(duration[0])
                    else :
                        continue
            elif len(duration) == 4 :
                    if duration[0] == "less" :
                        total_months = 6
                    elif duration[1] == "years" and duration[3] == "months" :
                        total_months = int(duration[0]) * 12 + int(duration[2]) 
                    else :
                        continue
            if total_months >= 0 and entry['title'] is not None: 
                    experience.add((year, total_months, entry['title']))

        
    # sort based on the yearmonth part of the tuple
    return sorted(experience)

def jobPaths(profileList):
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    jobPathList = []

    for profile in profileList:
        experience_data = profile['member_experience_collection']
        experience = extract_experience(experience_data, months)
        experience.append((None, None, profile['title'])) # current title is None for the first 2 tuple fields so I just appended to the end of the experience array
        jobPathList.append(experience)

    return jobPathList

jobPathList = jobPaths(profileList)


#first filter is just seeing if there is an exact match in it_job_synonyms array in the synonyms file,if there is an exact match in the array, then the title is replaced by the key 
def replace_synonyms(title):
    for synonym, synonyms_list in synonyms.it_job_synonyms.items():
        if title.lower() in synonyms_list:
            return synonym
    return title

#second filter sees if any value in the array exists in the title, then the key will replace the title
def replace_synonyms2(title):
    for synonym, synonyms_list in synonyms.it_job_synonyms2.items():
        if not title in synonyms.it_job_synonyms2 and any([x in title.lower() for x in synonyms_list]):
            return synonym
    return title

#third filter sees if all the array values exists in the title, then the key will replace the title
def replace_synonyms3(title):
    for synonym, synonyms_list in synonyms.it_job_synonyms3.items():
        if not title in synonyms.it_job_synonyms3 and all([x in title.lower() for x in synonyms_list]):
            return synonym
    return title

#first
jobPathList = [
    [(item[0], item[1], replace_synonyms(item[2])) for item in subarray]
    for subarray in jobPathList
]
#second
jobPathList = [
    [(item[0], item[1], replace_synonyms2(item[2])) for item in subarray]
    for subarray in jobPathList
]
#third
jobPathList = [
    [(item[0], item[1], replace_synonyms3(item[2])) for item in subarray]
    for subarray in jobPathList
]



#a dictionary of paths from one job to another and an array of months for that mapping the format is like (startJob, endJob):[months]
def create_job_mappings(jobPathList):
    job_mappings = {}

    for person in jobPathList:
        months1 = 0
        jobs1 = ''
        pair = set()

        for i in range(len(person)):
            if person[i][2] not in synonyms.it_job_synonyms3: #if the title is not in synonyms then go next
                continue

            jobs1 = person[i][2] 
            months1 += int(person[i][1] or 0) #months1 is the current months from the first entry of the array
            months2 = months1 + int(person[i][1] or 0) #months 2 is the distance from the months1, this way we can find distance from months2(end job) and months1(initial job)

            for j in range(i + 1, len(person)):
                if person[j][2] not in synonyms.it_job_synonyms3:
                    continue

                months2 += int(person[j][1] or 0)
                jobs2 = person[j][2]

                if jobs1 != jobs2 and (jobs1, jobs2) not in pair: #there cant be duplicate job mappings within a single person's career path, at least they won't be counted
                    pair.add((jobs1, jobs2))
                    difference = months2 - months1 - int(person[j][1] or 0)

                    if (jobs1, jobs2) in job_mappings:
                        job_mappings[(jobs1, jobs2)].append(difference)
                    else:
                        job_mappings[(jobs1, jobs2)] = [difference]

    return job_mappings
                    
def getJobs(arr) :
    return list(arr.keys())

#converts the mappings to a CSV format, should be mostly self explanatory
def tables(jobs, measure, dict) :
    mappings = []
    blank = ['']
    mappings.append(blank + jobs)

    for idx1 in range(len(jobs)) :
        job = [jobs[idx1]]
        for idx2 in range(len(jobs)) :
            if jobs[idx1] == jobs[idx2] :
                job.append(0)
            else :
                if ((jobs[idx1], jobs[idx2]) in dict) :
                    if measure == 'mean' :
                        job.append(int(statistics.mean(dict[(jobs[idx1], jobs[idx2])])))
                    elif measure == 'median' :
                        job.append(int(statistics.median(dict[(jobs[idx1], jobs[idx2])])))
                else :
                    job.append(0)
        mappings.append(job)

    return mappings                  



map = create_job_mappings(jobPathList)
jobs = getJobs(synonyms.it_job_synonyms3)
meanJobs = tables(jobs, 'mean', map)
medianJobs = tables(jobs, 'median', map)

#print(meanJobs)


with open('median.csv', 'w', newline='') as file:  #can generate mean.csv by taking replacing medianJobs with meanJobs
     writer = csv.writer(file)
     writer.writerows(medianJobs)




