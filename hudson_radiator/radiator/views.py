from django.shortcuts import render_to_response as render
from django.conf import settings
import models
# Create your views here.

def avg(lst):
    return sum(lst) / (1.0 * len(lst))


def get_radiator(request, build_list):
    build_types = [build_row.split(',') for build_row in build_list.split('|')]
    columnSize = 100 / len(build_types[0])
    return render('radiator/builds.html', locals())

def get_builds(request, build_type):
    builds = models.get_first_20(models.get_data(settings.HUDSON_URL + '/job/' + build_type + '_Build/api/json'))
    testProjects = models.get_test_projects(models.get_data(settings.HUDSON_URL + '/api/json?tree=jobs[name]'), build_type)
    smokeTests = [proj for proj in testProjects if proj.upper().find("SMOKE") > -1 ]
    otherTests = [proj for proj in testProjects if proj.upper().find("SMOKE") < 0 ]
    buildDict = dict((build.number,build) for build in builds)

    smokeBuilds = []
    for testName in smokeTests:
        smokeBuilds.extend(models.get_first_20(models.get_data(settings.HUDSON_URL + '/job/' + testName + '/api/json')))

    regressionBuilds = []
    for testName in otherTests:
        regressionBuilds.extend(models.get_first_20(models.get_data(settings.HUDSON_URL + '/job/' + testName + '/api/json')))

    for test in smokeBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            parent.smokeTests.append(test)

    for test in regressionBuilds:
        parent = buildDict.get(test.parent)

        if parent is not None:
            parent.regressionTests.append(test)
    
    avgTime = avg([build.duration for build in builds])
    if builds[0].status == 'BUILDING':
        progBarDone = (builds[0].runningTime / avgTime) * 100
        progBarLeft = 100 - progBarDone
    
    return render('radiator/builds_table.html', locals())