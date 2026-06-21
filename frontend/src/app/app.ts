import { Component,
  ChangeDetectorRef,
  Inject,
  Injectable,
  signal,
  PLATFORM_ID
} from '@angular/core';
import { Router, RouterOutlet, RouterLink } from '@angular/router';
import { NgClass, isPlatformBrowser } from '@angular/common';

import { Auth } from './auth'
import { Cookies } from './cookies'


// the level decides the color and icon shown in the notification
export type NotificationLevel = 'error' | 'warning' | 'success';

export interface NotificationItem {
  id: number;
  message: string;
  level: NotificationLevel;
}

// Shared notification service.
// Any component can inject this and call send_notification(message, level)
// to make a notification appear on the top-right corner for a few seconds.
@Injectable({ providedIn: 'root' })
export class Notifications {
  // list of notifications currently visible, rendered by app.html
  public list: NotificationItem[] = [];
  private next_id: number = 0;

  // shows a new notification and removes it automatically after a few seconds
  public send(message: string, level: NotificationLevel) : number {
    let id = this.next_id;
    this.next_id = this.next_id + 1;

    let notification: NotificationItem = {
      id: id,
      message: message,
      level: level
    };
    this.list.push(notification);
    return id;
  }

  // removes a single notification from the list
  public dismiss(id: number) {
    let remaining: NotificationItem[] = [];
    for (let notification of this.list) {
      if (notification.id != id) {
        remaining.push(notification);
      }
    }
    this.list = remaining;
  }
}

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, NgClass],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('frontend');
  constructor(
    private cookie_manager : Cookies,
    private router : Router,
    private cdr : ChangeDetectorRef,
    public notifications : Notifications,
    @Inject(PLATFORM_ID) private platformId: Object
  ){}

  // convenience wrapper so the layout can also raise notifications directly
  public send_notification(message: string, level: NotificationLevel) {
    let id = this.notifications.send(message, level);
    console.warn(message+' '+level);
    this.cdr.markForCheck();

    setTimeout(() => {
      this.notifications.dismiss(id);
      this.cdr.markForCheck();
    }, 4000);
  }

  ngOnInit() {
    this.update_data();
  }

  public update_data() {
    let plaintext_user_cookie = this.cookie_manager.getCookie('user');
    if(plaintext_user_cookie != null) {
      this.isLoggedIn = true;
      let obj_user_cookie = JSON.parse(plaintext_user_cookie);

      this.user_data.id = obj_user_cookie.id;
      this.user_data.firstname = obj_user_cookie.firstname;
      this.user_data.lastname = obj_user_cookie.lastname;
      this.user_data.id_institution = obj_user_cookie.id_institution;
      this.user_data.email = obj_user_cookie.email;
      this.user_data.role = obj_user_cookie.role;
    }
  }

  public isLoggedIn : boolean = false;
  user_data : UserData = {} as UserData;

  attempt_logout() {
    if(!isPlatformBrowser(this.platformId)) { return; }
    this.isLoggedIn = false;
    this.cdr.markForCheck();
    this.cookie_manager.deleteCookie('token');
    this.cookie_manager.deleteCookie('user');
    this.router.navigate(['login']);
  }

  links : link[] = [
    {
      text: 'Home',
      href: '/',
      loginRequired : false,
      icon: 'mdi mdi-home-outline'
    },
    {
      text: 'Create New Application',
      href: '/form',
      loginRequired : true,
      icon: 'mdi mdi-plus-circle-outline'
    },
    {
      text: 'Applications List',
      href: '/applications',
      loginRequired : true,
      icon: 'mdi mdi-card-multiple-outline'
    }
  ];

}

interface link {
  text: string;
  href: string;
  loginRequired : boolean;
  icon: string;
}

export interface UserData {
  id: number;
  firstname : string;
  lastname : string;
  role: string;
  email: string;
  id_institution : number;
}
