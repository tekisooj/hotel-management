import {NuxtAxiosInstance} from '@nuxtjs/axios';
import { defineNuxtPlugin } from 'nuxt/app';
import guestBff from 'api/guestBff';

export default defineNuxtPlugin((context, inject) => {
    const {$axios, $cookies, error: nuxtError} = context;

    const guestBffAxios = $axios.create({
        baseURL: `${context.env.GUEST_BFF_URL}/`
    })

})