<!--
HelpLink component

Last update: 2019-02-22
-->

<template>
  <span>
    <div v-if="label!==''" style="display:inline-block; font-size:1.4em; margin: 0px 5px 10px 0px;">{{ label }}</div> <!-- Was <h4> -->
      <button class="btn __blue small-button" @click="openLink(reflink)" :data-tooltip='$t("Help")' style="padding-top:2px; margin-bottom:5px">
        <i class="ti-help"></i>
      </button>
  </span>
</template>

<script>
  export default {
    name: 'help',
    
    props: {
      reflink: {
        type: String,
        default: ''
      }, 

      label: {
        type: String,
        default: ''
      }        
    },

    data() {
      return {
        baseURL: 'https://docs.google.com/document/d/1zB1_pX9ohKv0jTVLP-8NSvGVGWpX1tUNXmmvJHEvMkc/edit#heading=',
        linkMap: {
          'create-projects': 'h.oa2tji9979xf',
          'manage-projects': 'h.3h1iizobhq17',
          'inputs': 'h.ihv636',
          'scenarios': 'h.1v1yuxt',
          'optimizations': 'h.nmf14n',
          'geospatial': 'h.2lwamvv',
          'userguide': 'h.kp4pyp4hb8w6'
        }
      }
    },

    methods: {
      openLink(linkKey) {
        // Build the full link from the base URL and the specific link info.
        let fullLink = this.baseURL + this.linkMap[linkKey]
        
        // Set the parameters for a new browser window.
        let scrh = screen.height
        let scrw = screen.width
        let h = scrh * 0.8  // Height of window
        let w = scrw * 0.6  // Width of window
        let t = scrh * 0.1  // Position from top of screen -- centered
        let l = scrw * 0.37 // Position from left of screen -- almost all the way right

        // Open a new browser window.        
        let newWindow = window.open(fullLink, 
          'Reference manual', 'width=' + w + ', height=' + h + ', top=' + t + ',left=' + l)
          
        // If the main browser window is in focus, cause the new window to come into focus.
        if (window.focus) {
          newWindow.focus()
        }        
      }
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
