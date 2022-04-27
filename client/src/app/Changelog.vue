<template>

  <modal name="changelog-modal"
         height="auto"
         minHeight=300
         :classes="['v--modal', 'vue-dialog']"
         :width="width"
         :pivot-y="0.3"
         :adaptive="true"
         :scrollable="true"
         :clickToClose="false"
  >

    <div class="dialog-content">

      <vue-markdown>
        {{ content }}
      </vue-markdown>

      <button @click="close()" class='btn __red' style="display:inline-block">
        Close
      </button>

    </div>

  </modal>

</template>

<script>

  import VueMarkdown from 'vue-markdown'

  export default {

    name: 'Changelog',
    components: {VueMarkdown},

    data() {
      return {
        content: '',
      }
    },

    computed: {
      projectID() {
        return utils.projectID(this)
      },
      hasData() {
        return utils.hasData(this)
      },
    },

    async created() {
      try {
        let response = await this.$sciris.rpc('read_changelog');
        this.content = response.data;
      } catch (error) {
        this.content = "Error reading changelog";
      }
      this.$modal.show('changelog-modal');
    },

    methods: {

      close() {
        this.$emit('close')
      },
    }

  }
</script>

