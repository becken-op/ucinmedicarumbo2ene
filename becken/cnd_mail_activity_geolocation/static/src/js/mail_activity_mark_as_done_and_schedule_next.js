odoo.define('cnd_mail_activity_geolocation.ActivityScheduleNext', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;
    var Dialog = require('web.Dialog');
    
    const {
        registerInstancePatchModel,
        registerFieldPatchModel,
    } = require('mail/static/src/model/model_core.js');

    const { attr, one2one } = require('mail/static/src/model/model_field.js');

    registerInstancePatchModel('mail.activity', 'cnd_mail_activity_geolocation.ActivityScheduleNext', {
        /*
        async markAsDone({ attachments = [], feedback = false }) {
            const attachmentIds = attachments.map(attachment => attachment.id);
            // feedback = 'DONDE ESTAN PERROS: ' + feedback;
            await this.async(() => this.env.services.rpc({
                model: 'mail.activity',
                method: 'action_feedback',
                args: [[this.id]],
                kwargs: {
                    attachment_ids: attachmentIds,
                    feedback,
                },
            }));
            this.thread.refresh();
            this.delete();
        }*/
        async markAsDoneAndScheduleNext({ feedback }) {
            const feedbackParam = feedback;
            var self = this;

            const userAgent = (typeof navigator !== 'undefined' && navigator.userAgent) || '';
            const platform = (typeof navigator !== 'undefined' && navigator.platform) || '';
            const maxTouchPoints = (typeof navigator !== 'undefined' && navigator.maxTouchPoints) || 1;
            const isAndroid = /Android/.test(userAgent);
            const isIOS = /\b(iPad|iPhone|iPod)(?=;)/.test(userAgent) || (platform === 'MacIntel' && maxTouchPoints > 1);

            // Do not try to get geolocation in Odoo App (Android or IOS)
            if (userAgent.indexOf("AppleWebKit/537.36 (KHTML, like Gecko) Version") == -1 && 1==2) {
                var options = {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                };

                function toRad(Value) {
                    /** Converts numeric degrees to radians */
                    return Value * Math.PI / 180;
                }
                
                function distance(lon1, lat1, lon2, lat2) {
                    var R = 6371; // Radius of the earth in km
                    var dLat = toRad(lat2-lat1);  // Javascript functions in radians
                    var dLon = toRad(lon2-lon1); 
                    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * 
                            Math.sin(dLon/2) * Math.sin(dLon/2); 
                    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
                    var d = R * c; // Distance in km
                    return d*1000;
                }

                function showPosition(pos) {
                    var crd = pos.coords;
                    
                    console.log('Your current position is:');
                    console.log('Latitude : ' + crd.latitude);
                    console.log('Longitude: ' + crd.longitude);
                    console.log('More or less ' + crd.accuracy + ' meters.');
        
                    // https://www.meridianoutpost.com/resources/etools/calculators/calculator-latitude-longitude-distance.php?
                    var partner_latitude = 20.7264000;
                    var partner_longitude = -103.3873000;
                    
                    partner_latitude = 20.7596086;
                    partner_longitude = -103.3828138;
                    
                    var geolocation_maximum_distance_meters = 100.00;
                    
                    var distance_meters = distance(partner_longitude, partner_latitude, crd.longitude, crd.latitude);
                    
                    if (distance_meters > geolocation_maximum_distance_meters && 1 == 2) {
                        var activity = activityByType[self.type.id];
                        // alert(activity);
                        const message = _t('You must be at the customer''s home to be able to mark a visit as done. meters: '+ distance_meters.toString()+', Type ID: '+self.type.id+' Partner: '+self.request_partner_id);
                        Dialog.alert(this, message);
                        return;
                    }
                    else {
                        const action = self.async(() => self.env.services.rpc({
                            model: 'mail.activity',
                            method: 'action_feedback_schedule_next',
                            args: [[self.id]],
                            kwargs: {
                                feedback: feedbackParam,
                                check_in_latitude: crd.latitude,
                                check_in_longitude: crd.longitude,
                            },
                        }).then(function (result) {
                            // alert(action);
                            // alert('Yaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
                            // alert(self);
                            // self.thread.refresh();
                            // const thread = self.thread;
                            // // self.delete();
                            // if (!action) {
                            //     thread.refreshActivities();
                            //     return;
                            // }
                            // self.env.bus.trigger('do-action', {
                            //     action,
                            //     options: {
                            //         on_close: () => {
                            //             thread.refreshActivities();
                            //         },
                            //     },
                            // });
                            // self.delete();
                        }));
                        // alert('Yaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
                        self.thread.refresh();
                        const thread = self.thread;
                        // self.delete();
                        if (!action) {
                            thread.refreshActivities();
                            return;
                        }
                        self.env.bus.trigger('do-action', {
                            action,
                            options: {
                                on_close: () => {
                                    thread.refreshActivities();
                                },
                            },
                        });
                    }
                };

                function error(error) {
                    console.warn("ERROR(" + error.code + "): " + error.message);
                    const position = {
                        coords: {
                            latitude: 0.0,
                            longitude: 0.0,
                        },
                    };
                    showPosition(position);
                };

                navigator.geolocation.getCurrentPosition(showPosition, error, options);
            } else {
                const action = await this.async(() => this.env.services.rpc({
                    model: 'mail.activity',
                    method: 'action_feedback_schedule_next',
                    args: [[this.id]],
                    kwargs: { feedback },
                }));
                this.thread.refresh();
                const thread = this.thread;
                this.delete();
                if (!action) {
                    thread.refreshActivities();
                    return;
                }
                this.env.bus.trigger('do-action', {
                    action,
                    options: {
                        on_close: () => {
                            thread.refreshActivities();
                        },
                    },
                });
            }
        }

        // async markAsDone({ attachments = [], feedback = false }) {
        //     const attachmentIds = attachments.map(attachment => attachment.id);
        //     const feedbackParam = feedback;
        //     var self = this;
            
        //     const userAgent = (typeof navigator !== 'undefined' && navigator.userAgent) || '';
        //     const platform = (typeof navigator !== 'undefined' && navigator.platform) || '';
        //     const maxTouchPoints = (typeof navigator !== 'undefined' && navigator.maxTouchPoints) || 1;
        //     const isAndroid = /Android/.test(userAgent);
        //     const isIOS = /\b(iPad|iPhone|iPod)(?=;)/.test(userAgent) || (platform === 'MacIntel' && maxTouchPoints > 1);
            
        //     //var message1 = 'isAndroid: '+isAndroid.toString()+', isIOS: '+isIOS.toString()+', userAgent: '+userAgent+', platform: '+platform+', maxTouchPoints: '+maxTouchPoints.toString();
        //     //Dialog.alert(this, message1);
        //     if (userAgent.indexOf("AppleWebKit/537.36 (KHTML, like Gecko) Version") == -1) {
        //     // if (isIOS == false && isIOS == false) {
                
        //     var options = {
        //         enableHighAccuracy: true,
        //         timeout: 5000,
        //         maximumAge: 0
        //     };

        //     function toRad(Value) {
        //         /** Converts numeric degrees to radians */
        //         return Value * Math.PI / 180;
        //     }
            
        //     function distance(lon1, lat1, lon2, lat2) {
        //           var R = 6371; // Radius of the earth in km
        //           var dLat = toRad(lat2-lat1);  // Javascript functions in radians
        //           var dLon = toRad(lon2-lon1); 
        //           var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
        //                   Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * 
        //                   Math.sin(dLon/2) * Math.sin(dLon/2); 
        //           var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
        //           var d = R * c; // Distance in km
        //           return d*1000;
        //     }

        //     function showPosition(pos) {
        //         var crd = pos.coords;
                
        //         console.log('Your current position is:');
        //         console.log('Latitude : ' + crd.latitude);
        //         console.log('Longitude: ' + crd.longitude);
        //         console.log('More or less ' + crd.accuracy + ' meters.');
    
        //         // https://www.meridianoutpost.com/resources/etools/calculators/calculator-latitude-longitude-distance.php?
        //         var partner_latitude = 20.7264000;
        //         var partner_longitude = -103.3873000;
                
        //         partner_latitude = 20.7596086;
        //         partner_longitude = -103.3828138;
                
        //         var geolocation_maximum_distance_meters = 100.00;
                
        //         var distance_meters = distance(partner_longitude, partner_latitude, crd.longitude, crd.latitude);
                
        //         if (distance_meters > geolocation_maximum_distance_meters && 1 == 2) {
        //             var activity = activityByType[self.type.id];
        //             alert(activity);
        //             const message = _t('Debes estar en el domicilio del cliente para poder marcar como hecho una visita. Metros: '+ distance_meters.toString()+', Type ID: '+self.type.id+' Partner: '+self.request_partner_id);
        //             Dialog.alert(this, message);
        //             return;
        //         }
        //         else {

        //             self.async(() => self.env.services.rpc({
        //                 model: 'mail.activity',
        //                 method: 'action_feedback',
        //                 args: [[self.id]],
        //                 kwargs: {
        //                     attachment_ids: attachmentIds,
        //                     feedback: feedbackParam,
        //                     check_in_latitude: crd.latitude,
        //                     check_in_longitude: crd.longitude,
        //                 },
        //             }).then(function (result) {
        //                 self.thread.refresh();
        //                 //location.reload();
        //                 //self.delete();
        //             }));
        //         }
        //     };

        //     function error(error) {
        //         console.warn("ERROR(" + error.code + "): " + error.message);
        //         const position = {
        //             coords: {
        //                 latitude: 0.0,
        //                 longitude: 0.0,
        //             },
        //         };
        //         showPosition(position);
        //     };

        //     navigator.geolocation.getCurrentPosition(showPosition, error, options);
        //     } else {
        //         await this.async(() => this.env.services.rpc({
        //             model: 'mail.activity',
        //             method: 'action_feedback',
        //             args: [[this.id]],
        //             kwargs: {
        //                 attachment_ids: attachmentIds,
        //                 feedback: feedback,
        //             },
        //         }));
        //         this.thread.refresh();
        //         this.delete();
        //     }
        // }
    });
});
