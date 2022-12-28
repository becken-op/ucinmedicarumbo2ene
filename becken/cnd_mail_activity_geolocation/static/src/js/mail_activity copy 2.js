odoo.define('hr_attendance_geolocation.Activity', function (require) {
    'use strict';
    const {
        registerInstancePatchModel,
        registerFieldPatchModel,
    } = require('mail/static/src/model/model_core.js');
    const { attr, one2one } = require('mail/static/src/model/model_field.js');

    registerInstancePatchModel('mail.activity', 'hr_attendance_geolocation.Activity', {
        // var attachments;
        // var feedback;
        async markAsDone({ attachments = [], feedback = false }) {
            var self = this;
            // attachments = attachments;
            // feedback = feedback;
            var options = {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 60000,
            };
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    self._manual_attendance.bind(self),
                    self._getPositionError.bind(self),
                    options
                );
            }
        },

        // update_attendance: function () {
        //     var self = this;
        //     var options = {
        //         enableHighAccuracy: true,
        //         timeout: 5000,
        //         maximumAge: 60000,
        //     };
        //     if (navigator.geolocation) {
        //         navigator.geolocation.getCurrentPosition(
        //             self._manual_attendance.bind(self),
        //             self._getPositionError.bind(self),
        //             options
        //         );
        //     }
        // },
        _manual_attendance: function (position) {
            // const attachmentIds = attachments.map(attachment => attachment.id);
            // feedback = 'PEDRO: ' + feedback;
            this.async(() => this.env.services.rpc({
                model: 'mail.activity',
                method: 'action_feedback',
                args: [[this.id]],
                kwargs: {
                    attachment_ids: attachmentIds,
                    feedback: feedback,
                    check_in_latitude: position.coords.latitude,
                    check_in_longitude: position.coords.longitude,
                },
            }));
            this.thread.refresh();
            location.reload();
            this.delete();

            // var self = this;
            // this._rpc({
            //     model: "hr.employee",
            //     method: "attendance_manual",
            //     args: [
            //         [self.employee.id],
            //         "hr_attendance.hr_attendance_action_my_attendances",
            //         null,
            //         [position.coords.latitude, position.coords.longitude],
            //     ],
            // }).then(function (result) {
            //     if (result.action) {
            //         self.do_action(result.action);
            //     } else if (result.warning) {
            //         self.do_warn(result.warning);
            //     }
            // });
        },
        _getPositionError: function (error) {
            console.warn("ERROR(" + error.code + "): " + error.message);
            const position = {
                coords: {
                    latitude: 0.0,
                    longitude: 0.0,
                },
            };
            this._manual_attendance(position);
        },
    });
});


// odoo.define('hr_attendance_geolocation.Activity', function (require) {
//     "use strict";

//     var Activity = require('mail.Activity');

//     Activity.include({

//         /**
//          * @private
//          * @param {integer} activityID
//          * @param {string} feedback
//          * @param {integer[]} attachmentIds
//          * @return {Promise}
//          */
//         _sendActivityFeedback: function (activityID, feedback, attachmentIds) {
//             alert('_sendActivityFeedback');
//             feedback = 'HOLAS ' + feedback;
//             return self._super(activityID, feedback, attachmentIds);
//             // return this._rpc({
//             //     model: 'mail.activity',
//             //     method: 'action_feedback',
//             //     args: [[activityID]],
//             //     kwargs: {
//             //         feedback: feedback,
//             //         attachment_ids: attachmentIds || [],
//             //     },
//             //     context: this.record.getContext(),
//             // });
//         },

//         /**
//          * @param {Object} param0
//          * @param {mail.attachment[]} [param0.attachments=[]]
//          * @param {string|boolean} [param0.feedback=false]
//          */
//         async markAsDone({ attachments = [], feedback = false }) {
//             const attachmentIds = attachments.map(attachment => attachment.id);
//             feedback = 'DONDE ESTAN PERROS: ' + feedback;
//             await this.async(() => this.env.services.rpc({
//                 model: 'mail.activity',
//                 method: 'action_feedback',
//                 args: [[this.id]],
//                 kwargs: {
//                     attachment_ids: attachmentIds,
//                     feedback,
//                 },
//             }));
//             this.thread.refresh();
//             this.delete();
//         }
//     });

// });