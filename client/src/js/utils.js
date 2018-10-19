/**
 * Utilities that are shared across pages
 */

import rpcs from '@/js/rpc-service'
import status from '@/js/status-service'

function sleep(time) {
  // Return a promise that resolves after _time_ milliseconds.
  return new Promise((resolve) => setTimeout(resolve, time));
}

function getUniqueName(fileName, otherNames) {
  let tryName = fileName
  let numAdded = 0
  while (otherNames.indexOf(tryName) > -1) {
    numAdded = numAdded + 1
    tryName = fileName + ' (' + numAdded + ')'
  }
  return tryName
}

function updateSorting(vm, sortColumn) {
  console.log('updateSorting() called')
  if (vm.sortColumn === sortColumn) { // If the active sorting column is clicked...
    vm.sortReverse = !vm.sortReverse // Reverse the sort.
  } else { // Otherwise.
    vm.sortColumn = sortColumn // Select the new column for sorting.
    vm.sortReverse = false // Set the sorting for non-reverse.
  }
}

function placeholders(startVal) {
  var indices = []
  if (!startVal) {
    startVal = 0
  }
  for (var i = startVal; i <= 100; i++) {
    indices.push(i);
  }
  return indices;
}

function projectID(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    let projectID = vm.$store.state.activeProject.project.id
    return projectID
  }
}

function hasData(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return false
  }
  else {
    return vm.$store.state.activeProject.project.hasData
  }
}

function simStart(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    return vm.$store.state.activeProject.project.sim_start
  }
}

function simEnd(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    return vm.$store.state.activeProject.project.sim_end
  }
}

function simYears(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return []
  } else {
    var sim_start = vm.$store.state.activeProject.project.sim_start
    var sim_end = vm.$store.state.activeProject.project.sim_end
    var years = []
    for (var i = sim_start; i <= sim_end; i++) {
      years.push(i);
    }
    console.log('sim years: ' + years)
    return years;
  }
}

function activePops(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    let pop_pairs = vm.$store.state.activeProject.project.pops
    let pop_list = ["All"]
    for(let i = 0; i < pop_pairs.length; ++i) {
      pop_list.push(pop_pairs[i][1]);
    }
    return pop_list
  }
}

function getPlotOptions(vm) {
  console.log('getPlotOptions() called')
  let project_id = projectID(vm)
  rpcs.rpc('get_supported_plots', [project_id, true])
    .then(response => {
      vm.plotOptions = response.data // Get the parameter values
    })
    .catch(error => {
      status.fail(vm, 'Could not get plot options', error)
    })
}

function makeGraphs(vm, graphdata) {
  let waitingtime = 0.5
  console.log('makeGraphs() called')
  status.start(vm) // Start indicating progress.
  vm.hasGraphs = true
  sleep(waitingtime * 1000)
    .then(response => {
      var n_plots = graphdata.length
      console.log('Rendering ' + n_plots + ' graphs')
      for (var index = 0; index <= n_plots; index++) {
        console.log('Rendering plot ' + index)
        var divlabel = 'fig' + index
        var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
        while (div.firstChild) {
          div.removeChild(div.firstChild);
        }
        try {
          console.log(graphdata[index]);
          mpld3.draw_figure(divlabel, graphdata[index], function (fig, element) {
            fig.setXTicks(6, function (d) {
              return d3.format('.0f')(d);
            });
            // fig.setYTicks(null, function (d) {
            //   return d3.format('.2s')(d);
            // });
          });
        }
        catch (error) {
          console.log('Making graphs failed: ' + error.message);
        }
      }
    })
  status.succeed(vm, 'Graphs created') // Indicate success.
}

function clearGraphs(vm, numfigs) {
  console.log('clearGraphs() called')
  for (let index = 1; index <= numfigs; index++) {
    let divlabel = 'fig' + index
    let div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
    if (div) {
      while (div.firstChild) {
        div.removeChild(div.firstChild);
      }
    } else {
      console.log('WARNING: div not found: ' + divlabel)
    }
    vm.hasGraphs = false
  }
}

function exportGraphs(vm, project_id, cache_id) {
  console.log('exportGraphs() called')
  rpcs.download('export_graphs', [project_id, cache_id]) // Make the server call to download the framework to a .prj file.
    .catch(error => {
      status.fail(vm, 'Could not download graphs', error)
    })
}

function exportResults(vm, project_id, cache_id) {
  console.log('exportResults()')
  rpcs.download('export_results', [project_id, cache_id]) // Make the server call to download the framework to a .prj file.
    .catch(error => {
      status.fail(vm, 'Could not export results', error)
    })
}


//
// Graphs DOM functions
//

function scaleElem(svg, frac) {
  // It might ultimately be better to redraw the graph, but this works
  var width  = svg.getAttribute("width")
  var height = svg.getAttribute("height")
  var viewBox = svg.getAttribute("viewBox")
  if (!viewBox) {
    svg.setAttribute("viewBox",  '0 0 ' + width + ' ' + height)
  }
  // if this causes the image to look weird, you may want to look at "preserveAspectRatio" attribute
  svg.setAttribute("width",  width*frac)
  svg.setAttribute("height", height*frac)
}

function scaleFigs(frac) {
  var graphs = window.top.document.querySelectorAll('svg.mpld3-figure')
  for (var g = 0; g < graphs.length; g++) {
    scaleElem(graphs[g], frac)
  }
}

function updateDatasets(vm) {
  return new Promise((resolve, reject) => {
    console.log('updateDatasets() called')
    rpcs.rpc('get_dataset_keys', [vm.projectID]) // Get the current user's datasets from the server.
      .then(response => {
        vm.datasetOptions = response.data // Set the scenarios to what we received.
        if (vm.datasetOptions.indexOf(vm.activeDataset) === -1) {
          console.log('Dataset ' + vm.activeDataset + ' no longer found')
          vm.activeDataset = vm.datasetOptions[0] // If the active dataset no longer exists in the array, reset it
        } else {
          console.log('Dataset ' + vm.activeDataset + ' still found')
        }
        vm.newDatsetName = vm.activeDataset // WARNING, KLUDGY
        console.log('Datset options: ' + vm.datasetOptions)
        console.log('Active dataset: ' + vm.activeDataset)
      })
      .catch(error => {
        status.fail(this, 'Could not get dataset info', error)
        reject(error)
      })
  })
}

export default {
  sleep,
  getUniqueName,
  placeholders,
  updateSorting,
  projectID,
  hasData,
  simStart,
  simEnd,
  simYears,
  activePops,
  getPlotOptions,
  makeGraphs,
  clearGraphs,
  exportGraphs,
  exportResults,
  scaleFigs,
  updateDatasets,
}