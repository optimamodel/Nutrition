<template>
  <div class="locale-switcher">
    🌐
    <select v-model="$i18n.locale" @change="setLocale">
      <option v-for='entry in this.locales' :value="entry.locale">
        {{ entry.name }}
      </option>
    </select>
  </div>
</template>

<script>

import i18n from '../i18n'
import utils from '../js/utils.js'

export default {
  name: "LocaleSwitcher",

  data() {
    return {
      locales: utils.locales,
    }
},

  methods: {
    setLocale() {
      console.log('Set language')
      localStorage.setItem("lang", i18n.locale);
    },
  }
}
</script>